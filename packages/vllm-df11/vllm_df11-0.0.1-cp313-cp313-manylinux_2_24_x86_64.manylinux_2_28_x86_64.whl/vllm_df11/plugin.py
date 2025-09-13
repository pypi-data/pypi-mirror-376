import logging
from typing import Any

logger = logging.getLogger("vllm.plugins.df11")


def register() -> Any:
    """vLLM general plugin entry point for DF11."""
    try:
        # Importing these modules triggers registration via decorators
        # and sets up the custom ops used by DF11 quant methods.
        from vllm_df11 import loader as _  # noqa: F401
        from vllm_df11.quantization import DF11Config  # noqa: F401

        # Optionally register a quantization config name for DF11.
        try:
            from vllm.model_executor.layers.quantization import (
                register_quantization_config,
            )
            register_quantization_config("df11")(DF11Config)
        except Exception:
            # It's fine if already registered or not needed
            pass

        logger.info("df11 plugin: loader and quantization registered")
    except Exception:
        # Do not raise to avoid killing vLLM boot
        logger.exception("df11 plugin failed to register components")

    return None
