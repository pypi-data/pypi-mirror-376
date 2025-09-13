import math
import os
import sys
from typing import Optional

import torch
from torch.nn import Parameter

from vllm.logger import init_logger
from vllm.model_executor.layers.linear import LinearMethodBase
from vllm.model_executor.layers.quantization.base_config import (
    QuantizationConfig,
    QuantizeMethodBase,
)
from vllm.model_executor.layers.vocab_parallel_embedding import (
    VocabParallelEmbedding,
)
from vllm.model_executor.layers.utils import dispatch_unquantized_gemm
from vllm.utils import direct_register_custom_op


logger = init_logger(__name__)


try:  # pragma: no cover - optional import for compilation control
    from torch._dynamo import disable as dynamo_disable  # type: ignore
    from torch._dynamo import allow_in_graph as dynamo_allow_in_graph  # type: ignore
except Exception:  # noqa: E722

    def dynamo_disable(fn):  # type: ignore
        return fn

    def dynamo_allow_in_graph(fn):  # type: ignore
        return fn


# Attempt to locate the DF11 extension near the vLLM repo if available
try:
    repo_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
    )
    df11_path = os.path.join(repo_root, "DF11")
    if df11_path not in sys.path:
        sys.path.insert(0, df11_path)
except Exception:
    df11_path = None  # type: ignore


def _import_df11_extension(): # WIP
    """Try to import DF11 extension.

    Strategy:
    1) regular import if in PYTHONPATH/site-packages
    2) locate DF11 dir next to installed vllm package
    3) locate DF11 dir computed relative to this plugin (best-effort)
    """
    import importlib

    # 1) try in-package extension first
    try:
        return importlib.import_module("vllm_df11.dfloat11_decode_v2")
    except Exception:
        pass

    # 1b) regular import without package (legacy installs)
    try:
        return importlib.import_module("dfloat11_decode_v2")
    except Exception:
        pass

    # 2) try alongside installed vllm package
    try:
        import vllm as _vllm

        vllm_pkg_dir = os.path.dirname(_vllm.__file__)  # .../vllm/vllm
        vllm_repo_root = os.path.dirname(vllm_pkg_dir)  # .../vllm
        df11_dir = os.path.join(vllm_repo_root, "DF11")
        if os.path.isdir(df11_dir):
            # search for any matching .so
            for fname in os.listdir(df11_dir):
                if fname.startswith("dfloat11_decode_v2") and fname.endswith(".so"):
                    sys.path.insert(0, df11_dir)
                    try:
                        return importlib.import_module("dfloat11_decode_v2")
                    except Exception:
                        break
            # also check common build subdir
            build_dir = os.path.join(df11_dir, "build")
            if os.path.isdir(build_dir):
                for root, _dirs, files in os.walk(build_dir):
                    for fname in files:
                        if fname.startswith("dfloat11_decode_v2") and fname.endswith(
                            ".so"
                        ):
                            sys.path.insert(0, root)
                            try:
                                return importlib.import_module("dfloat11_decode_v2")
                            except Exception:
                                pass
    except Exception:
        pass

    # 3) try the best-effort path computed above
    if df11_path is not None and os.path.isdir(df11_path):
        for fname in os.listdir(df11_path):
            if fname.startswith("dfloat11_decode_v2") and fname.endswith(".so"):
                sys.path.insert(0, df11_path)
                try:
                    return importlib.import_module("dfloat11_decode_v2")
                except Exception:
                    break
        build_dir = os.path.join(df11_path, "build")
        if os.path.isdir(build_dir):
            for root, _dirs, files in os.walk(build_dir):
                for fname in files:
                    if fname.startswith("dfloat11_decode_v2") and fname.endswith(".so"):
                        sys.path.insert(0, root)
                        try:
                            return importlib.import_module("dfloat11_decode_v2")
                        except Exception:
                            pass

    return None


dfloat11_decode_v2 = _import_df11_extension()
if dfloat11_decode_v2 is None:
    logger.warning(
        "DF11: dfloat11_decode_v2 extension not found. Ensure DF11 build artifacts are available."
    )
def _current_stream_ptr(device: torch.device | str | None) -> int:
    try:
        if device is None:
            stream = torch.cuda.current_stream()
        else:
            if isinstance(device, str):
                device = torch.device(device)
            stream = torch.cuda.current_stream(device)
        # In PyTorch 2.x, Stream.cuda_stream returns an integer pointer value
        return int(getattr(stream, "cuda_stream"))
    except Exception:
        return 0



def _apply_df11_embedding(
    indices: torch.Tensor,
    luts: torch.Tensor,
    encoded_exponent: torch.Tensor,
    sign_mantissa: torch.Tensor,
    output_positions: torch.Tensor,
    gaps: torch.Tensor,
    threads_per_block: int,
    bytes_per_thread: int,
    shared_mem_size: int,
    num_embeddings: int,
    embedding_dim: int,
    dtype: Optional[torch.dtype] = None,
) -> torch.Tensor:
    assert dfloat11_decode_v2 is not None, "DF11 extension missing at runtime"
    device = encoded_exponent.device
    n_elements = sign_mantissa.numel()
    n_bytes = encoded_exponent.numel()
    n_luts = int(luts.shape[0])
    out = _TensorManager.get(device, n_elements)
    threads = int(threads_per_block)
    blocks = int(math.ceil(n_bytes / (threads * int(bytes_per_thread))))
    dfloat11_decode_v2.decode(
        luts.data_ptr(),
        encoded_exponent.data_ptr(),
        sign_mantissa.data_ptr(),
        output_positions.data_ptr(),
        gaps.data_ptr(),
        out.data_ptr(),
        n_luts,
        n_bytes,
        n_elements,
        blocks,
        threads,
        shared_mem_size,
        _current_stream_ptr(device),
    )
    weight_2d = out.view(num_embeddings, embedding_dim)
    if dtype is None:
        dtype = weight_2d.dtype
    return torch.embedding(weight_2d.to(dtype), indices)


try:
    # Avoid duplicate registration if core already registered ops
    existing = None
    try:
        existing = getattr(torch.ops, "vllm")._apply_df11_embedding  # type: ignore[attr-defined]
    except Exception:
        existing = None

    def _fake_df11_embedding(
        indices: torch.Tensor,
        luts: torch.Tensor,
        encoded_exponent: torch.Tensor,
        sign_mantissa: torch.Tensor,
        output_positions: torch.Tensor,
        gaps: torch.Tensor,
        threads_per_block: int,
        bytes_per_thread: int,
        shared_mem_size: int,
        num_embeddings: int,
        embedding_dim: int,
        dtype: Optional[torch.dtype] = None,
    ) -> torch.Tensor:
        out_dtype = dtype or torch.bfloat16
        out_shape = tuple(list(indices.shape) + [int(embedding_dim)])
        return torch.empty(out_shape, dtype=out_dtype, device=indices.device)

    if existing is None:
        direct_register_custom_op(
            op_name="_apply_df11_embedding",
            op_func=_apply_df11_embedding,
            mutates_args=[],
            fake_impl=_fake_df11_embedding,
        )
        apply_df11_embedding_op = torch.ops.vllm._apply_df11_embedding
    else:
        apply_df11_embedding_op = existing
except Exception as e:  # pragma: no cover
    logger.warning("DF11: failed to register custom embedding op: %s", e)
    apply_df11_embedding_op = None


def _df11_decode(
    luts: torch.Tensor,
    encoded_exponent: torch.Tensor,
    sign_mantissa: torch.Tensor,
    output_positions: torch.Tensor,
    gaps: torch.Tensor,
    threads_per_block: int,
    bytes_per_thread: int,
    shared_mem_size: int,
    n_elements: int,
    dtype: Optional[torch.dtype] = None,
) -> torch.Tensor:
    assert dfloat11_decode_v2 is not None, "DF11 extension missing at runtime"
    device = encoded_exponent.device
    n_bytes = encoded_exponent.numel()
    n_luts = int(luts.shape[0])
    out = _TensorManager.get(device, int(n_elements))
    threads = int(threads_per_block)
    blocks = int(math.ceil(n_bytes / (threads * int(bytes_per_thread))))
    dfloat11_decode_v2.decode(
        luts.data_ptr(),
        encoded_exponent.data_ptr(),
        sign_mantissa.data_ptr(),
        output_positions.data_ptr(),
        gaps.data_ptr(),
        out.data_ptr(),
        n_luts,
        n_bytes,
        int(n_elements),
        blocks,
        threads,
        int(shared_mem_size),
        _current_stream_ptr(device),
    )
    if dtype is not None and out.dtype != dtype:
        return out.to(dtype)
    return out


def _fake_df11_decode(
    luts: torch.Tensor,
    encoded_exponent: torch.Tensor,
    sign_mantissa: torch.Tensor,
    output_positions: torch.Tensor,
    gaps: torch.Tensor,
    threads_per_block: int,
    bytes_per_thread: int,
    shared_mem_size: int,
    n_elements: int,
    dtype: Optional[torch.dtype] = None,
) -> torch.Tensor:
    fake_dtype = dtype or torch.bfloat16
    return torch.empty(
        (int(n_elements),), dtype=fake_dtype, device=encoded_exponent.device
    )


try:
    # Avoid duplicate registration if core already registered ops
    existing = None
    try:
        existing = getattr(torch.ops, "vllm")._df11_decode  # type: ignore[attr-defined]
    except Exception:
        existing = None
    if existing is None:
        direct_register_custom_op(
            op_name="_df11_decode",
            op_func=_df11_decode,
            mutates_args=[],
            fake_impl=_fake_df11_decode,
        )
        df11_decode_op = torch.ops.vllm._df11_decode
    else:
        df11_decode_op = existing
except Exception as e:  # pragma: no cover
    logger.warning("DF11: failed to register decode op: %s", e)
    df11_decode_op = None


class _TensorManager:
    _buffers: dict[torch.device, torch.Tensor] = {}

    @staticmethod
    def get(device: torch.device, n_elements: int) -> torch.Tensor:
        if isinstance(device, str):
            device = torch.device(device)
        buf = _TensorManager._buffers.get(device)
        if buf is None or buf.numel() < n_elements:
            buf = torch.empty(n_elements, dtype=torch.bfloat16, device=device)
            _TensorManager._buffers[device] = buf
        return buf[:n_elements]


class DF11Config(QuantizationConfig):
    def get_name(self) -> str:  # type: ignore[override]
        return "df11"

    def get_supported_act_dtypes(self) -> list[torch.dtype]:  # type: ignore[override]
        return [torch.float16, torch.bfloat16]

    @classmethod
    def get_min_capability(cls) -> int:  # type: ignore[override]
        return 70

    @staticmethod
    def get_config_filenames() -> list[str]:  # type: ignore[override]
        return []

    @classmethod
    def from_config(cls, config: dict) -> "DF11Config":  # type: ignore[override]
        return cls()


class DF11LinearMethod(LinearMethodBase):
    def __init__(self,threads_per_block: tuple[int, ...], bytes_per_thread: int):
        super().__init__()
        self.threads_per_block = tuple(threads_per_block)
        self.bytes_per_thread = int(bytes_per_thread)

    def create_weights(self, layer: torch.nn.Module, *args, **kwargs):  # noqa: D401
        if not hasattr(layer, "weight"):
            layer.register_parameter(
                "weight",
                Parameter(torch.empty(0, dtype=torch.bfloat16), requires_grad=False),
            )

    def _decode_into(self, layer: torch.nn.Module) -> torch.Tensor:
        n_elements = int(layer.sign_mantissa.numel())
        if df11_decode_op is not None:
            return df11_decode_op(
                layer.luts,
                layer.encoded_exponent,
                layer.sign_mantissa,
                layer.output_positions,
                layer.gaps,
                int(self.threads_per_block[0]),
                int(self.bytes_per_thread),
                int(layer.shared_mem_size),
                int(n_elements),
                torch.bfloat16,
            )
        assert dfloat11_decode_v2 is not None, "DF11 CUDA extension is not available"
        device = layer.encoded_exponent.device
        out = _TensorManager.get(device, n_elements)
        n_bytes = layer.encoded_exponent.numel()
        n_luts = layer.luts.shape[0]
        blocks_per_grid = int(
            math.ceil(n_bytes / (self.threads_per_block[0] * self.bytes_per_thread))
        )
        dfloat11_decode_v2.decode(
            layer.luts.data_ptr(),
            layer.encoded_exponent.data_ptr(),
            layer.sign_mantissa.data_ptr(),
            layer.output_positions.data_ptr(),
            layer.gaps.data_ptr(),
            out.data_ptr(),
            n_luts,
            n_bytes,
            n_elements,
            blocks_per_grid,
            self.threads_per_block[0],
            layer.shared_mem_size,
            _current_stream_ptr(device),
        )
        return out

    @dynamo_disable
    @dynamo_allow_in_graph
    def apply(
        self,
        layer: torch.nn.Module,
        x: torch.Tensor,
        bias: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        decoded = self._decode_into(layer)
        if hasattr(layer, "output_size") and hasattr(layer, "input_size"):
            out_features = int(layer.output_size)
            in_features = int(layer.input_size)
        elif hasattr(layer, "out_features") and hasattr(layer, "in_features"):
            out_features = int(layer.out_features)
            in_features = int(layer.in_features)
        else:
            in_features = x.shape[-1]
            out_features = decoded.numel() // in_features
        weight_2d = decoded.view(out_features, in_features)
        return dispatch_unquantized_gemm()(layer, x, weight_2d, bias)


class DF11EmbeddingMethod(DF11LinearMethod):
    def embedding(
        self, layer: VocabParallelEmbedding, indices: torch.Tensor
    ) -> torch.Tensor:
        if apply_df11_embedding_op is not None:
            return apply_df11_embedding_op(
                indices,
                layer.luts,
                layer.encoded_exponent,
                layer.sign_mantissa,
                layer.output_positions,
                layer.gaps,
                int(self.threads_per_block[0]),
                int(self.bytes_per_thread),
                int(layer.shared_mem_size),
                int(layer.num_embeddings),
                int(layer.embedding_dim),
                torch.bfloat16,
            )
        decoded = self._decode_into(layer)
        weight_2d = decoded.view(layer.num_embeddings, layer.embedding_dim)
        return torch.embedding(weight_2d, indices)


class DF11LinearSplitMethod(DF11LinearMethod):
    def __init__(
        self,
        threads_per_block: tuple[int, ...],
        bytes_per_thread: int,
        parent: torch.nn.Module,
        start_index: int,
        end_index: int
    ):
        super().__init__(
            threads_per_block=threads_per_block, bytes_per_thread=bytes_per_thread
        )
        self._parent = parent
        self._start = int(start_index)
        self._end = int(end_index)

    @dynamo_disable
    def _decode_into(self, layer: torch.nn.Module) -> torch.Tensor:  # type: ignore[override]
        full = super()._decode_into(self._parent)
        return full[self._start : self._end]


def df11_apply_linear(
    layer: torch.nn.Module, x: torch.Tensor, bias: Optional[torch.Tensor]
):
    method = getattr(layer, "quant_method", None)
    src = getattr(method, "_parent", layer)
    n_elements = int(src.sign_mantissa.numel())
    if df11_decode_op is not None:
        full = df11_decode_op(
            src.luts,
            src.encoded_exponent,
            src.sign_mantissa,
            src.output_positions,
            src.gaps,
            int(
                method.threads_per_block[0]
                if hasattr(method, "threads_per_block")
                else 256
            ),
            int(method.bytes_per_thread if hasattr(method, "bytes_per_thread") else 16),
            int(src.shared_mem_size),
            int(n_elements),
            torch.bfloat16,
        )
    else:
        assert dfloat11_decode_v2 is not None, "DF11 CUDA extension is not available"
        device = src.encoded_exponent.device
        full = _TensorManager.get(device, n_elements)
        n_bytes = src.encoded_exponent.numel()
        n_luts = src.luts.shape[0]
        threads = int(method.threads_per_block[0])
        blocks = int(math.ceil(n_bytes / (threads * int(method.bytes_per_thread))))
        dfloat11_decode_v2.decode(
            src.luts.data_ptr(),
            src.encoded_exponent.data_ptr(),
            src.sign_mantissa.data_ptr(),
            src.output_positions.data_ptr(),
            src.gaps.data_ptr(),
            full.data_ptr(),
            n_luts,
            n_bytes,
            n_elements,
            blocks,
            threads,
            int(src.shared_mem_size),
            _current_stream_ptr(device),
        )
    if hasattr(method, "_start") and hasattr(method, "_end"):
        decoded = full[int(method._start) : int(method._end)]
    else:
        decoded = full
    if hasattr(layer, "output_size") and hasattr(layer, "input_size"):
        out_features = int(layer.output_size)
        in_features = int(layer.input_size)
    elif hasattr(layer, "out_features") and hasattr(layer, "in_features"):
        out_features = int(layer.out_features)
        in_features = int(layer.in_features)
    else:
        in_features = x.shape[-1]
        out_features = decoded.numel() // in_features
    weight_2d = decoded.view(out_features, in_features)
    return dispatch_unquantized_gemm()(layer, x, weight_2d, bias)
