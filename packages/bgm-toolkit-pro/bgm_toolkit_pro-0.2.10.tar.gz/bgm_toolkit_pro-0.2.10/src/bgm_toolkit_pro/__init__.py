from importlib import import_module, metadata
_pkg = import_module("bgm_toolkit")
globals().update({k: getattr(_pkg, k) for k in dir(_pkg) if not k.startswith("_")})
try:
    __version__ = metadata.version("bgm-toolkit-pro")
except Exception:
    __version__ = getattr(_pkg, "__version__", "0.0.0")
