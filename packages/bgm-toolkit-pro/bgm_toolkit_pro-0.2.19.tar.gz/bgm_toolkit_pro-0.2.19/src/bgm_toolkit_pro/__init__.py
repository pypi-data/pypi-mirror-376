from importlib.metadata import PackageNotFoundError, version as _dist_version
try:
    __version__ = _dist_version('bgm-toolkit-pro')
except PackageNotFoundError:
    __version__ = '0.0.0'

def __getattr__(name):
    import importlib
    try:
        core = importlib.import_module('bgm_toolkit')
    except ModuleNotFoundError as e:
        raise AttributeError(f"'bgm_toolkit_pro' needs 'bgm_toolkit' for attribute {name!r}") from e
    return getattr(core, name)
