def test_imports():
    import bingbong_api
    from bingbong_api import BingBongClient, DEFAULT_BASE_URL, MissingAPIKeyError, APIRequestError
    assert DEFAULT_BASE_URL
