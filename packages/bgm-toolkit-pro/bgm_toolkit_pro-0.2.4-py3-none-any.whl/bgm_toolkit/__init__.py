from importlib import metadata as _md

__all__ = []
try:
    __version__ = _md.version("bgm-toolkit-pro")
except _md.PackageNotFoundError:
    __version__ = "0.0.0"
