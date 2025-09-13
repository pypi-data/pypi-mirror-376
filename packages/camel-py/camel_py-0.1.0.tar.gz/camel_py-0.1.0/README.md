# 🐪 Camel-ollama

A lightweight Python client for [Ollama](https://ollama.ai/) that makes it easy to:

- Chat with models (supports streaming or one-shot responses).
- Persist and reload conversation context.
- Manage models (list, pull, delete).
- Generate embeddings.

---

## 🚀 Installation

```bash
pip install camel
```

## Quickstart example

```Python
from camel import CamelClient

with CamelClient(model="llama3") as client:
    # Simple one-shot response
    resp = client.chat("Hello, who are you?")
    print(resp.text)

    # Streaming response
    print("Assistant: ", end="")
    resp = client.stream("Tell me a joke about camels")
    print(resp.text)

```

## 📂 Examples

See the [examples/](examples/) directory for more examples.
- [advanced_chat.py](examples/advanced_chat.py) → context persistence across sessions

## 🔧 Features

- Streaming API: real-time token streaming (.stream()).
- Context management: save/load/clear conversation history.
- Model management: list, pull, and delete Ollama models.
- Embeddings: generate embeddings for text.
