def test_import():
    import importlib.metadata as md, bgm_toolkit_pro
    assert isinstance(md.version("bgm-toolkit-pro"), str)
    assert isinstance(getattr(bgm_toolkit_pro, "__version__", ""), str)
