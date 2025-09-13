class MissingAPIKeyError(ValueError):
    """Raised when no API key is provided or discovered in the environment."""
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or (
            "BingBong API key not provided. "
            "Set the BINGBONG_API_KEY environment variable or pass api_key="..." to BingBongClient(api_key=...)."
        ))


class APIRequestError(RuntimeError):
    """Raised when an API call fails with an HTTP error or unexpected response."""
    pass
