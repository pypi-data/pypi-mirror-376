from __future__ import annotations

from typing import Any, Dict, Optional, Union

from langchain_core.runnables import Runnable

from .client import TokenCrushClient, CrushResponse


RunnableInput = Union[str, Dict[str, Any]]


class RunnableTokenCrush(Runnable[RunnableInput, CrushResponse]):
	"""LangChain Runnable wrapper around TokenCrush /v1/crush.

	Input: str or {"prompt": str}
	Output: CrushResponse (pydantic model)
	"""

	lc_namespace = ["tokencrush", "runnable"]

	def __init__(self, api_key: str, *, base_url: Optional[str] = None, fallback_to_input: bool = False) -> None:
		self._client = TokenCrushClient(api_key=api_key, base_url=base_url)
		self._fallback = fallback_to_input

	def invoke(self, input: RunnableInput, config: Optional[dict] = None, **kwargs: Any) -> CrushResponse:  # type: ignore[override]
		prompt: Optional[str]
		if isinstance(input, str):
			prompt = input
		elif isinstance(input, dict):
			prompt = input.get("prompt") if isinstance(input.get("prompt"), str) else None
		else:
			prompt = None

		if not prompt or not prompt.strip():
			raise ValueError("RunnableTokenCrush.invoke: input must be a non-empty string or { 'prompt': str }")

		try:
			return self._client.crush({"prompt": prompt})
		except Exception:
			if self._fallback:
				# Simple heuristic token estimate (4 chars/token)
				length = max(1, round(len(prompt.strip()) / 4))
				return CrushResponse(
					optimized_prompt=prompt,
					input_tokens=length,
					output_tokens=length,
					percentage_reduction=0.0,
				)
			raise

	def __del__(self) -> None:
		try:
			self._client.close()
		except Exception:
			pass


__all__ = ["RunnableTokenCrush"]
