# TNSA API Text

Minimal Python SDK for TNSA AI text generation.

## Installation

```bash
pip install tnsa-api-text
```

## Usage

```python
from tnsa_api_text import TNSA

# Initialize client
client = TNSA(
    api_key="your-api-key",
    base_url="https://api.tnsaai.com"
)

# Generate text
response = client.generate(
    prompt="Hello, how are you?",
    model="NGen3.9-Pro"
)
print(response)

# Chat format
response = client.chat([
    {"role": "user", "content": "Hello!"}
])
print(response)

# List models
models = client.models()
print(models)

# Streaming
stream = client.generate(
    prompt="Tell me a story",
    stream=True
)
for line in stream.iter_lines():
    if line:
        print(line.decode())
```

## Methods

- `generate(prompt, model, temperature, max_tokens, stream)` - Generate text
- `chat(messages, model, temperature, max_tokens)` - Chat with messages
- `models()` - List available models
- `close()` - Close session