# CygnisAI Python SDK

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Simonc44/cygnisai_sdk_python?color=blue&label=version)](https://github.com/Simonc44/cygnisai_sdk_python/releases)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-brightgreen)](https://github.com/Simonc44/cygnisai_sdk_python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Status](https://img.shields.io/github/actions/workflow/status/Simonc44/cygnisai_sdk_python/tests.yml?label=tests)](https://github.com/Simonc44/cygnisai_sdk_python/actions)
[![Documentation](https://img.shields.io/badge/docs-view-brightgreen)](https://simonc44.github.io/cygnisai_sdk_python/)

The simplest, fastest way to integrate CygnisAI language models into your Python projects.

> **Note:** API access is currently in **private beta**. Key creation is not yet open to the public.

---

## Installation

```bash
pip install cygnis-sdk-python
```
With git :
```bash
pip install git+https://github.com/Simonc44/cygnisai_sdk_python.git
```

---

## Quick Start

```python
import cygnisai_sdk_python as cygnis

cygnis.configure(api_key="YOUR_API_KEY")

model = cygnis.GenerativeModel("alpha2")
response = model.generate_content("Give me a Python tip.")
print(response.text)
```

### Environment variable

Set `CYGNIS_API_KEY` and call `configure()` without arguments:

```python
import cygnisai_sdk_python as cygnis

cygnis.configure()          # reads CYGNIS_API_KEY automatically
model = cygnis.GenerativeModel("alpha2")
```

---

## Streaming

```python
stream = model.generate_content("Tell me a story.", stream=True)

import asyncio

async def main():
    async for token in stream:
        print(token, end="", flush=True)

asyncio.run(main())
```

---

## Async usage

```python
import asyncio
import cygnisai_sdk_python as cygnis

cygnis.configure(api_key="YOUR_API_KEY")
model = cygnis.GenerativeModel("alpha2")

async def main():
    response = await model.async_generate_content("Hello!")
    print(response.text)
    print(f"Latency: {response.latency_ms} ms")
    print(f"Tokens used: {response.usage.total_tokens}")

asyncio.run(main())
```

---

## Low-level client

```python
import asyncio
from cygnisai_sdk_python import CygnisAIClient, ChatRequest, Message

async def main():
    async with CygnisAIClient(api_key="YOUR_KEY") as client:
        request = ChatRequest(
            model="alpha2",
            prompt="What is 2+2?",
            messages=[Message(role="user", content="What is 2+2?")],
        )
        response = await client.chat(request)
        print(response.response)

asyncio.run(main())
```

---

## Error handling

```python
import cygnisai_sdk_python as cygnis

cygnis.configure(api_key="YOUR_KEY")
model = cygnis.GenerativeModel("alpha2")

try:
    response = model.generate_content("Hello!")
except cygnis.AuthenticationError:
    print("Invalid API key.")
except cygnis.RateLimitError:
    print("Too many requests — slow down.")
except cygnis.ServerError as e:
    print(f"Server error {e.status_code}: {e.message}")
except cygnis.NetworkError:
    print("Could not reach the API.")
except cygnis.CygnisAIError as e:
    print(f"Unexpected SDK error: {e}")
```

---

## Configuration options

| Parameter | Type | Default | Description |
|---|---|---|---|
| `api_key` | `str` | `CYGNIS_API_KEY` env var | Your secret API key |
| `base_url` | `str` | production URL | Override the API base URL |
| `timeout` | `float` | `30.0` | HTTP timeout in seconds |
| `max_retries` | `int` | `3` | Retries on transient errors (429, 5xx) |

---

## Available Models

| Model | Description | Status |
|---|---|---|
| **`alpha_v01`** | Initial test version, lightweight prototyping | Stable |
| **`alpha1`** | Balanced, optimised for response speed | Stable |
| **`alpha2`** | Most capable, recommended for complex reasoning | Stable |

---

## Feature Status

- [x] Simple interface (`GenerativeModel`) 
- [x] Streaming (`stream=True`)
- [x] Async-native client with context manager
- [x] Automatic retries with exponential backoff
- [x] Environment-variable API key
- [x] Typed exceptions (`AuthenticationError`, `RateLimitError`, …)
- [x] Pydantic v2 validation
- [x] `py.typed` marker (PEP 561)
- [ ] Public access (closed beta)

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

---

## Licence

MIT — see `LICENCE` for details.
