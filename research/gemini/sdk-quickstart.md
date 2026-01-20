# Google GenAI SDK Quickstart

The `google-genai` SDK is Google's official Python library for accessing Gemini models. It provides a unified interface for both the Gemini Developer API and Vertex AI.

## Installation

```bash
pip install google-genai
```

For async support:
```bash
pip install google-genai[aiohttp]
```

## Important: Legacy SDK Deprecation

The older `google-generativeai` package reached end-of-life on **November 30, 2025**. Always use `google-genai` for new projects.

**Migration checklist:**
- ❌ `import google.generativeai` → ✅ `from google import genai`
- ❌ `genai.configure(api_key=...)` → ✅ `genai.Client(api_key='...')`
- ❌ `model.generate_content()` → ✅ `client.models.generate_content()`

## Client Setup

### Option 1: Gemini Developer API (Recommended for Getting Started)

```python
from google import genai

# Explicit API key
client = genai.Client(api_key='YOUR_GEMINI_API_KEY')

# Or use environment variable GEMINI_API_KEY or GOOGLE_API_KEY
client = genai.Client()
```

Get your API key from [Google AI Studio](https://aistudio.google.com/).

### Option 2: Vertex AI (Enterprise)

```python
from google import genai

client = genai.Client(
    vertexai=True,
    project='your-gcp-project-id',
    location='us-central1'  # or other supported region
)
```

Environment variables for Vertex AI:
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`

## Basic Text Generation

```python
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Explain how neural networks learn'
)

print(response.text)
```

## Model Selection

| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| `gemini-3-pro-preview` | Complex reasoning | Slower | Higher |
| `gemini-3-flash-preview` | General purpose | Fast | Lower |
| `gemini-2.5-flash` | Legacy/stable | Fast | Lower |
| `gemini-2.5-flash-lite` | Ultra-low latency | Fastest | Lowest |

**Recommendation:** Start with `gemini-3-flash-preview` for most tasks.

## Multimodal Input

### Text + Image

```python
from google import genai
from google.genai import types
from PIL import Image

client = genai.Client(api_key='YOUR_API_KEY')

# Load image
image = Image.open('photo.jpg')

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
        image,
        'Describe what you see in this image'
    ]
)

print(response.text)
```

### From Bytes

```python
with open('document.pdf', 'rb') as f:
    pdf_bytes = f.read()

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
        types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
        'Summarize this document'
    ]
)
```

### From URL/URI

```python
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
        types.Part.from_uri(
            file_uri='gs://your-bucket/video.mp4',
            mime_type='video/mp4'
        ),
        'What happens in this video?'
    ]
)
```

## Chat Conversations

### Basic Chat

```python
chat = client.chats.create(model='gemini-3-flash-preview')

# First message
response = chat.send_message('Hello! Can you help me learn Python?')
print(response.text)

# Follow-up (maintains context)
response = chat.send_message('What are decorators?')
print(response.text)

# View conversation history
for message in chat.get_history():
    print(f"{message.role}: {message.parts[0].text}")
```

### Chat with System Instruction

```python
from google.genai import types

chat = client.chats.create(
    model='gemini-3-flash-preview',
    config=types.GenerateContentConfig(
        system_instruction='You are a helpful coding tutor. Give concise answers with code examples.'
    )
)

response = chat.send_message('How do I read a JSON file?')
print(response.text)
```

## Configuration Options

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Write a creative story about a robot',
    config=types.GenerateContentConfig(
        # Sampling parameters
        temperature=1.0,        # Creativity (0.0-2.0, default 1.0)
        top_k=40,               # Top-k sampling
        top_p=0.95,             # Nucleus sampling

        # Output control
        max_output_tokens=1000, # Maximum response length
        stop_sequences=['THE END'],  # Stop generation triggers

        # System behavior
        system_instruction='You are a creative writer.',

        # Reasoning depth (Gemini 3)
        thinking_level='high'   # 'minimal', 'low', 'medium', 'high'
    )
)
```

## Streaming Responses

For faster time-to-first-token:

```python
# Synchronous streaming
for chunk in client.models.generate_content_stream(
    model='gemini-3-flash-preview',
    contents='Write a long essay about climate change'
):
    print(chunk.text, end='', flush=True)
```

## Structured Output (JSON)

```python
from pydantic import BaseModel
from typing import List

class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    instructions: List[str]
    prep_time_minutes: int

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Give me a recipe for chocolate chip cookies',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=Recipe
    )
)

# Parse the response
recipe = Recipe.model_validate_json(response.text)
print(f"Recipe: {recipe.name}")
print(f"Prep time: {recipe.prep_time_minutes} minutes")
```

## Error Handling

```python
from google.genai.errors import APIError

try:
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents='Hello'
    )
    print(response.text)
except APIError as e:
    print(f"API Error {e.code}: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | API key for Gemini Developer API |
| `GOOGLE_API_KEY` | Alternative API key variable |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (Vertex AI) |
| `GOOGLE_CLOUD_LOCATION` | GCP region (Vertex AI) |

## Next Steps

- [Advanced Features](./sdk-advanced-features.md) - Async, streaming, caching
- [Function Calling](./function-calling.md) - Tools and code execution
- [Image Generation](./image-generation.md) - Generate images with Gemini 3

## References

- [Official SDK Documentation](https://googleapis.github.io/python-genai/)
- [GitHub Repository](https://github.com/googleapis/python-genai)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
