"""
SMLR - Simple Image Compression Tool using DCT
"""

from .smlr import SMLR

try:
    # Python 3.8+
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
except Exception:
    # Python 3.7 fallback (requires importlib_metadata dependency)
    from importlib_metadata import version as _pkg_version, PackageNotFoundError  # type: ignore

try:
    __version__ = _pkg_version("smlr")
except PackageNotFoundError:
    # Package metadata not available in editable installs without build
    __version__ = "0.0.0"

__all__ = ["SMLR"]
