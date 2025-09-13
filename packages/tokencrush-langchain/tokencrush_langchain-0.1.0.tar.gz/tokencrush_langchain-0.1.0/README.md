## tokencrush-langchain (Python)

LangChain-compatible Python client for TokenCrush prompt optimization API.

- TokenCrushClient: thin HTTP client for `POST /v1/crush`
- RunnableTokenCrush: a Runnable that accepts a prompt and returns the optimization result

### Install

```bash
pip install tokencrush-langchain
```

### Usage

```python
from tokencrush_langchain import TokenCrushClient, RunnableTokenCrush

client = TokenCrushClient(api_key="YOUR_API_KEY")
res = client.crush({"prompt": "Summarize the following document ..."})
print(res.optimized_prompt)

crush = RunnableTokenCrush(api_key="YOUR_API_KEY")
result = crush.invoke("Rewrite this prompt to be concise while preserving meaning ...")
print(result.optimized_prompt)
```

### API Contract

`POST /v1/crush` with JSON body `{ "prompt": string }` and `Authorization: Bearer <api key>`.

Successful response shape:

```json
{
  "optimized_prompt": "Optimized version of your prompt",
  "input_tokens": 10,
  "output_tokens": 6,
  "percentage_reduction": 40
}
```

Notes:
- Only prompts with more than 20 tokens are optimized.
- If similarity is below 80%, the original prompt is returned.
- API may temporarily disable optimization for keys with poor performance.

### Options

- base_url: override API base (default `https://api.tokencrush.ai`)
- fallback_to_input (Runnable): if API fails, return original prompt with 0% reduction

### License

MIT


