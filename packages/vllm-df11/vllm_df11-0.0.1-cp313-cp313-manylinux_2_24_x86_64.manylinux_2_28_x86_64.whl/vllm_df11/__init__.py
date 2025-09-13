from .plugin import register

try:  # pragma: no cover
    from . import dfloat11_decode_v2  # type: ignore
except Exception:  # noqa: E722
    dfloat11_decode_v2 = None  # type: ignore

__all__ = ["register"]
