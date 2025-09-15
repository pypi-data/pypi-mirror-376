from __future__ import annotations

# Re-export public API from mlx_gen_parity for backward/forward compatibility
import mlx_gen_parity as _m
from mlx_gen_parity import *  # noqa: F401,F403

__all__ = _m.__all__
__version__ = _m.__version__

