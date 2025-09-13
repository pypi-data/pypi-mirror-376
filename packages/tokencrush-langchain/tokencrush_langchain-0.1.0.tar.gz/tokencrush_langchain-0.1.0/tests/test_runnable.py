import types

import pytest

import tokencrush_langchain.runnable as runnable_mod
from tokencrush_langchain.client import CrushResponse


class StubClient:
	def __init__(self, *args, **kwargs):
		pass

	def crush(self, data):
		prompt = data["prompt"]
		if prompt == "boom":
			raise RuntimeError("fail")
		return CrushResponse(
			optimized_prompt=prompt.upper(),
			input_tokens=10,
			output_tokens=5,
			percentage_reduction=50.0,
		)

	def close(self):
		pass


def test_runnable_invokes_and_returns_response(monkeypatch):
	monkeypatch.setattr(runnable_mod, "TokenCrushClient", StubClient)
	r = runnable_mod.RunnableTokenCrush(api_key="k")
	res = r.invoke("hello world")
	assert res.optimized_prompt == "HELLO WORLD"


def test_runnable_accepts_object_input(monkeypatch):
	monkeypatch.setattr(runnable_mod, "TokenCrushClient", StubClient)
	r = runnable_mod.RunnableTokenCrush(api_key="k")
	res = r.invoke({"prompt": "hi"})
	assert res.output_tokens == 5


def test_runnable_fallbacks_to_input(monkeypatch):
	monkeypatch.setattr(runnable_mod, "TokenCrushClient", StubClient)
	r = runnable_mod.RunnableTokenCrush(api_key="k", fallback_to_input=True)
	res = r.invoke("boom")
	assert res.optimized_prompt == "boom"
	assert res.percentage_reduction == 0.0


def test_runnable_raises_on_invalid_input(monkeypatch):
	monkeypatch.setattr(runnable_mod, "TokenCrushClient", StubClient)
	r = runnable_mod.RunnableTokenCrush(api_key="k")
	with pytest.raises(ValueError):
		# @ts-expect-error equivalent not needed; passing wrong type intentionally
		r.invoke({})
