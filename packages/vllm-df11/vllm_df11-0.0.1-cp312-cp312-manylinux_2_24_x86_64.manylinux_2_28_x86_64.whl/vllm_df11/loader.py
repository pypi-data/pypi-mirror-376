import os
import re
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
from huggingface_hub import snapshot_download
from safetensors.torch import load_file
from tqdm import tqdm

from vllm.config import ModelConfig
from vllm.logger import init_logger
from vllm.model_executor.layers.linear import LinearBase
from vllm.model_executor.layers.vocab_parallel_embedding import (
    ParallelLMHead, VocabParallelEmbedding,
)
from vllm.model_executor.model_loader.base_loader import BaseModelLoader
from vllm.model_executor.model_loader.utils import (
    initialize_model,
    process_weights_after_loading,
    set_default_torch_dtype,
)

from vllm.model_executor.model_loader import register_model_loader

from .quantization import (
    DF11EmbeddingMethod,
    DF11LinearMethod,
    DF11LinearSplitMethod,
    df11_apply_linear,
)


logger = init_logger(__name__)


@register_model_loader("df11")
class DF11ModelLoader(BaseModelLoader):
    """Model loader for DF11-compressed checkpoints."""

    COMPRESSED_SUFFIXES = {
        "encoded_exponent",
        "sign_mantissa",
        "luts",
        "output_positions",
        "gaps",
        "split_positions",
    }

    def download_model(self, model_config: ModelConfig) -> None:
        model_path = model_config.model
        if os.path.exists(model_path):
            return
        logger.info("Downloading DF11 model %s from HF Hub", model_path)
        local_dir = model_path.replace("/", "__")
        snapshot_download(model_path, local_dir=local_dir, repo_type="model")
        model_config.model = local_dir

    def load_weights(self, model: nn.Module, model_config: ModelConfig) -> None:
        from transformers.models.auto.configuration_auto import AutoConfig

        model_path = model_config.model
        cfg = AutoConfig.from_pretrained(model_path)
        if not hasattr(cfg, "dfloat11_config"):
            raise ValueError("Checkpoint lacks dfloat11_config; not a DF11 model")

        df_cfg: Dict = cfg.dfloat11_config
        threads_per_block: Tuple[int, ...] = tuple(df_cfg["threads_per_block"])
        bytes_per_thread: int = int(df_cfg["bytes_per_thread"])
        pattern_dict: Dict[str, List[str] | None] = df_cfg["pattern_dict"]

        compressed: Dict[str, Dict[str, torch.Tensor]] = {}
        safetensor_files = [
            f for f in os.listdir(model_path) if f.endswith(".safetensors")
        ]
        for fname in tqdm(safetensor_files, desc="Reading DF11 safetensors"):
            loaded = load_file(os.path.join(model_path, fname))
            for tname, tvalue in loaded.items():
                layer_path, component = self.parse_compressed_tensor_name(tname)
                if layer_path is None:
                    # direct param/buffer copy if shapes match
                    named_params = dict(model.named_parameters())
                    named_bufs = dict(model.named_buffers())
                    if tname in named_params:
                        param = named_params[tname]
                        if param.shape == tvalue.shape:
                            param.data.copy_(tvalue)
                    elif tname in named_bufs:
                        buf = named_bufs[tname]
                        if buf.shape == tvalue.shape:
                            buf.copy_(tvalue)
                    continue
                compressed.setdefault(layer_path, {})[component] = tvalue

        for layer_path, comp in compressed.items():
            module = self.resolve_module(model, layer_path)

            # Register buffers
            for name, tensor in comp.items():
                if name == "split_positions":
                    setattr(module, name, tensor.tolist())
                else:
                    module.register_buffer(name, tensor)

            # Compute shared memory size if positions available
            if "output_positions" in comp:
                op = comp["output_positions"]
                op_u32 = op.view(torch.uint32)
                diff_max = (op_u32[1:].to(torch.int64) -
                            op_u32[:-1].to(torch.int64)).max().item()
                shared_mem = int(threads_per_block[0]) * 4 + 4 + int(diff_max) * 2
                module.shared_mem_size = int(shared_mem)

            # Assign DF11 methods for modules with compressed weights
            if "encoded_exponent" in comp:
                if isinstance(module, (VocabParallelEmbedding, ParallelLMHead)):
                    module.quant_method = DF11EmbeddingMethod(
                        threads_per_block=threads_per_block,
                        bytes_per_thread=bytes_per_thread,
                    )
                    if hasattr(module, "weight"):
                        try:
                            delattr(module, "weight")
                        except Exception:
                            pass
                elif isinstance(module, LinearBase):
                    module.quant_method = DF11LinearMethod(
                        threads_per_block=threads_per_block,
                        bytes_per_thread=bytes_per_thread,
                    )
                    try:
                        module.quant_method.apply = df11_apply_linear  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    if hasattr(module, "weight"):
                        try:
                            delattr(module, "weight")
                        except Exception:
                            pass
                else:
                    # merged module case
                    assigned = False

                    def _get_vllm_groups(attr_names: List[str]) -> List[Tuple[str, int, int]]:
                        name_to_idx: Dict[str, int] = {
                            name: i for i, name in enumerate(attr_names)
                        }
                        groups: List[Tuple[str, int, int]] = []

                        def get(name: str) -> int | None:
                            return name_to_idx.get(name)

                        qi, ki, vi = (
                            get("self_attn.q_proj"),
                            get("self_attn.k_proj"),
                            get("self_attn.v_proj"),
                        )
                        if qi is not None and ki is not None and vi is not None:
                            start = min(qi, ki, vi)
                            end = max(qi, ki, vi) + 1
                            groups.append(("self_attn.qkv_proj", start, end))

                        oi = get("self_attn.o_proj")
                        if oi is not None:
                            groups.append(("self_attn.o_proj", oi, oi + 1))

                        gi, ui = get("mlp.gate_proj"), get("mlp.up_proj")
                        if gi is not None and ui is not None:
                            start = min(gi, ui)
                            end = max(gi, ui) + 1
                            groups.append(("mlp.gate_up_proj", start, end))

                        di = get("mlp.down_proj")
                        if di is not None:
                            groups.append(("mlp.down_proj", di, di + 1))

                        return groups

                    for pattern, attr_names in pattern_dict.items():
                        if re.fullmatch(pattern, layer_path) and attr_names is not None:
                            if not hasattr(module, "split_positions"):
                                raise RuntimeError(
                                    f"DF11: split_positions missing for merged module {layer_path}")
                            split_positions = getattr(module, "split_positions")
                            cuts = [0] + [int(x) for x in split_positions] + [
                                int(module.sign_mantissa.numel())
                            ]

                            if not attr_names:
                                assigned = True
                                break

                            groups = _get_vllm_groups(attr_names)

                            if not groups:
                                # 1:1 mapping fallback
                                for i, attr_path in enumerate(attr_names):
                                    target = module
                                    for p in attr_path.split('.'):
                                        target = getattr(target, p)
                                    if isinstance(target, LinearBase):
                                        target.quant_method = DF11LinearSplitMethod(
                                            threads_per_block=threads_per_block,
                                            bytes_per_thread=bytes_per_thread,
                                            parent=module,
                                            start_index=cuts[i],
                                            end_index=cuts[i + 1],
                                        )
                                        if hasattr(target, "weight"):
                                            try:
                                                delattr(target, "weight")
                                            except Exception:
                                                pass
                                assigned = True
                                break

                            for target_path, seg_start, seg_end in groups:
                                start_elem = cuts[seg_start]
                                end_elem = cuts[seg_end]

                                target = module
                                for p in target_path.split('.'):
                                    target = getattr(target, p)

                                if isinstance(target, LinearBase):
                                    target.quant_method = DF11LinearSplitMethod(
                                        threads_per_block=threads_per_block,
                                        bytes_per_thread=bytes_per_thread,
                                        parent=module,
                                        start_index=start_elem,
                                        end_index=end_elem,
                                    )
                                    try:
                                        target.quant_method.apply = df11_apply_linear  # type: ignore[attr-defined]
                                    except Exception:
                                        pass
                                    if hasattr(target, "weight"):
                                        try:
                                            delattr(target, "weight")
                                        except Exception:
                                            pass
                            assigned = True
                            break

                    if not assigned:
                        module.quant_method = DF11LinearMethod(
                            threads_per_block=threads_per_block,
                            bytes_per_thread=bytes_per_thread,
                        )
                        try:
                            module.quant_method.apply = df11_apply_linear  # type: ignore[attr-defined]
                        except Exception:
                            pass

        logger.info("DF11 weights registered and DF11 methods assigned")

    def load_model(self, vllm_config, model_config: ModelConfig) -> nn.Module:
        device_config = vllm_config.device_config
        target_device = torch.device(
            self.load_config.device or device_config.device or "cuda")

        with set_default_torch_dtype(model_config.dtype):
            # Initialize on CPU to avoid allocating dense GPU weights
            with torch.device("cpu"):
                model = initialize_model(vllm_config=vllm_config,
                                         model_config=model_config)

            # Register DF11 buffers and quant methods
            self.load_weights(model, model_config)

            # Post-process and move model
            process_weights_after_loading(model, model_config, target_device)
            model.to(target_device)
            logger.info("DF11 model loaded onto %s", str(target_device))
            return model.eval()

    @staticmethod
    def parse_compressed_tensor_name(name):
        for suffix in DF11ModelLoader.COMPRESSED_SUFFIXES:
            if name.endswith("." + suffix):
                return name[: -len(suffix) - 1], suffix
        return None, None

    @staticmethod
    def resolve_module(root: nn.Module, dotted: str) -> nn.Module:
        mod = root
        for part in dotted.split("."):
            if not hasattr(mod, part):
                raise RuntimeError(
                    f"Failed to resolve module path {dotted} (missing {part})")
            mod = getattr(mod, part)
        return mod

    @staticmethod
    def prepare_weight_injection(module: nn.Module, layer_path: str,
                                 pattern_dict: Dict[str, List[str] | None]):
        # The current loader assigns quant methods directly; this helper is kept
        # for compatibility if external callers need to pre-strip weights.
        if isinstance(module, (nn.Linear, nn.Embedding, VocabParallelEmbedding,
                               ParallelLMHead)):
            if hasattr(module, "weight"):
                delattr(module, "weight")
            return
        matched_attrs: List[str] | None = None
        for pattern, attrs in pattern_dict.items():
            if re.fullmatch(pattern, layer_path):
                matched_attrs = attrs
                break
        if matched_attrs is None:
            return
        if not matched_attrs:
            if hasattr(module, "weight"):
                delattr(module, "weight")
            return
        module.weight_injection_modules = []  # type: ignore[attr-defined]
        for attr_path in matched_attrs:
            sub = module
            ok = True
            for part in attr_path.split("."):
                if hasattr(sub, part):
                    sub = getattr(sub, part)
                else:
                    ok = False
                    break
            if not ok:
                continue
            if hasattr(sub, "weight"):
                delattr(sub, "weight")
            module.weight_injection_modules.append(sub)  # type: ignore[attr-defined]


