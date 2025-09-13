# bingbong_api

A minimal, typed Python client for the (placeholder) **BingBong API**.

> Note: This is a scaffold intended to be customized for the real BingBong API.

## Installation

```bash
# From the project root
pip install -e .
```

## Configuration

The client **requires** an API key. You can provide it in one of three ways:

1. Pass `api_key="..."` to `BingBongClient(...)`
2. Set the environment variable `BINGBONG_API_KEY`
3. Store it in a `.env` file (see `.env.example`) and load it via your preferred method (e.g., `python-dotenv`)

If the key is missing, an exception with a clear, professional message is raised.

## Usage

```python
from bingbong_api import BingBongClient

client = BingBongClient()  # reads BINGBONG_API_KEY from env if not provided
res = client.get_placeholder(resource="status")
print(res.status_code, res.json())

echo = client.post_placeholder(resource="echo", json={"hello": "world"})
print(echo.status_code, echo.json())
```

## Customization

- Update `base_url` to the actual BingBong API origin.
- Replace `get_placeholder` / `post_placeholder` with concrete endpoints.
- Add pydantic or dataclasses to model request/response payloads if you want stronger typing.

## License

MIT
