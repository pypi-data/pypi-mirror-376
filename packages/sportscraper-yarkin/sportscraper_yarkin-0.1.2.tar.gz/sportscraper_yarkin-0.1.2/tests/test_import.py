def test_import():
    import sportscraper
    assert hasattr(sportscraper, "__version__")