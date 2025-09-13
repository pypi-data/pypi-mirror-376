import json

import httpx
import pytest

from tokencrush_langchain.client import TokenCrushClient, CrushRequest


class _MockTransport(httpx.BaseTransport):
	def __init__(self, handler):
		self._handler = handler

	def handle_request(self, request: httpx.Request) -> httpx.Response:  # type: ignore[override]
		return self._handler(request)


def test_client_calls_api_with_bearer_token():
	def handler(req: httpx.Request) -> httpx.Response:
		assert req.method == "POST"
		assert req.url.path == "/v1/crush"
		assert req.headers.get("authorization") == "Bearer test-key"
		body = json.loads(req.content)
		assert body == {"prompt": "Hello"}
		payload = {
			"optimized_prompt": "opt",
			"input_tokens": 10,
			"output_tokens": 6,
			"percentage_reduction": 40,
		}
		return httpx.Response(200, json=payload)

	transport = _MockTransport(handler)
	client = TokenCrushClient("test-key", base_url="https://api.tokencrush.ai", http_client=httpx.Client(transport=transport))
	res = client.crush(CrushRequest(prompt="Hello"))
	assert res.optimized_prompt == "opt"


def test_client_raises_on_error():
	def handler(req: httpx.Request) -> httpx.Response:
		return httpx.Response(401, text="Bad key")

	transport = _MockTransport(handler)
	client = TokenCrushClient("k", http_client=httpx.Client(transport=transport))
	with pytest.raises(httpx.HTTPStatusError):
		client.crush({"prompt": "hi"})
