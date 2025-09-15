def test_import():
    import importlib.metadata as md, bgm_labour
    assert isinstance(md.version("bgm-toolkit-labour"), str)
    assert hasattr(bgm_labour, "__all__")
