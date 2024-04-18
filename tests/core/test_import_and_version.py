def test_import_and_version():
    import rlp

    assert isinstance(rlp.__version__, str)
