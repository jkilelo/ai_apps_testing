# Gemini 3 API Reference

Technical reference for Gemini 3 API parameters, configuration options, and usage patterns.

## Model Identifiers

```
gemini-3-pro-preview          # Complex reasoning tasks
gemini-3-flash-preview        # Fast, cost-effective
gemini-3-pro-image-preview    # Image generation (Nano Banana Pro)
```

## Context Windows & Limits

| Model | Input Tokens | Output Tokens | Knowledge Cutoff |
|-------|--------------|---------------|------------------|
| Pro | 1,000,000 | 64,000 | January 2025 |
| Flash | 1,000,000 | 64,000 | January 2025 |
| Pro Image | 65,000 | 32,000 | January 2025 |

## Thinking Level Parameter

The `thinking_level` parameter controls the depth of the model's internal reasoning process before generating a response.

### Available Levels

**Gemini 3 Pro:**
| Level | Description | Use Case |
|-------|-------------|----------|
| `low` | Minimizes latency and cost | Simple tasks, chat, high-throughput |
| `high` (default) | Maximizes reasoning depth | Complex reasoning, analysis |

**Gemini 3 Flash:**
| Level | Description | Use Case |
|-------|-------------|----------|
| `minimal` | Near-zero thinking overhead | Ultra-low latency chat |
| `low` | Minimal reasoning | Simple instruction following |
| `medium` | Balanced approach | General-purpose tasks |
| `high` (default) | Maximum reasoning | Complex problems |

### Usage Example

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='YOUR_API_KEY')

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Solve this logic puzzle...',
    config=types.GenerateContentConfig(
        thinking_level='high'  # or 'minimal', 'low', 'medium'
    )
)
```

### Important Notes
- Gemini 3 models use dynamic thinking by default (`thinking_level='high'`)
- Higher thinking levels increase latency but improve response quality
- The legacy `thinkingBudget` parameter is accepted for backwards compatibility but may result in suboptimal performance

## Media Resolution Options

Control how images and videos are tokenized:

| Parameter | Image Tokens | Video Tokens | Use Case |
|-----------|--------------|--------------|----------|
| `media_resolution_low` | 280 | 70 | Fast processing, cost savings |
| `media_resolution_medium` | 560 | 70 | Balanced quality/cost |
| `media_resolution_high` | 1,120 | 280 | Detailed analysis |
| `media_resolution_ultra_high` | Custom | Custom | Maximum fidelity |

### Usage Example

```python
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents=[
        types.Part.from_uri(
            file_uri='gs://bucket/image.jpg',
            mime_type='image/jpeg'
        ),
        'Analyze this image in detail'
    ],
    config=types.GenerateContentConfig(
        media_resolution='high'
    )
)
```

## Temperature Configuration

**Recommendation:** Keep temperature at its default value of `1.0` for Gemini 3 models.

Lower temperatures may cause:
- Response looping
- Degraded output quality
- Inconsistent behavior

```python
# Default (recommended)
config = types.GenerateContentConfig(
    temperature=1.0
)

# Only adjust if specifically needed
config = types.GenerateContentConfig(
    temperature=0.7  # Slightly more deterministic
)
```

## Thought Signatures

Thought signatures maintain reasoning context across multi-turn interactions. They are encrypted representations of the model's internal thought process.

### Requirements by Feature

| Feature | Signature Requirement |
|---------|----------------------|
| Function Calling | **Required** - 400 error if missing |
| Image Generation | **Required** - 400 error if missing |
| Text/Chat | Recommended - degrades quality if missing |

### Automatic Handling

When using official SDKs with standard chat history, thought signatures are handled automatically:

```python
# Signatures managed automatically
chat = client.chats.create(model='gemini-3-pro-preview')
response = chat.send_message('Hello')
response = chat.send_message('Continue our conversation')
```

### Manual Handling

For custom implementations, preserve and return signatures:

```python
# First request
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Analyze this problem...'
)

# Extract thought signature from response
thought_signature = response.thought_signature

# Subsequent request - include signature
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents=[
        # Previous context with signature
        types.Content(
            role='model',
            parts=[response.parts[0]],
            thought_signature=thought_signature
        ),
        # New message
        types.Content(
            role='user',
            parts=[types.Part.from_text('Continue...')]
        )
    ]
)
```

## Safety Settings

Configure content filtering thresholds:

```python
from google.genai import types

config = types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category='HARM_CATEGORY_HARASSMENT',
            threshold='BLOCK_MEDIUM_AND_ABOVE'
        ),
        types.SafetySetting(
            category='HARM_CATEGORY_HATE_SPEECH',
            threshold='BLOCK_MEDIUM_AND_ABOVE'
        ),
        types.SafetySetting(
            category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
            threshold='BLOCK_MEDIUM_AND_ABOVE'
        ),
        types.SafetySetting(
            category='HARM_CATEGORY_DANGEROUS_CONTENT',
            threshold='BLOCK_MEDIUM_AND_ABOVE'
        )
    ]
)
```

### Threshold Options
- `BLOCK_NONE` - No blocking
- `BLOCK_LOW_AND_ABOVE` - Block low+ probability harmful content
- `BLOCK_MEDIUM_AND_ABOVE` - Block medium+ probability (default)
- `BLOCK_HIGH_AND_ABOVE` - Only block high probability harmful content

## System Instructions

Provide persistent context for the model:

```python
response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Explain quantum entanglement',
    config=types.GenerateContentConfig(
        system_instruction='You are a physics professor. Explain concepts clearly using analogies. Keep responses under 200 words.'
    )
)
```

## Structured Output (JSON Mode)

Force responses to conform to a schema:

```python
from pydantic import BaseModel
from typing import List

class MovieReview(BaseModel):
    title: str
    rating: float
    pros: List[str]
    cons: List[str]

response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Review the movie Inception',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_schema=MovieReview
    )
)

# Parse response
review = MovieReview.model_validate_json(response.text)
```

## Pricing Reference

### Gemini 3 Pro
| Context Size | Input (per 1M) | Output (per 1M) |
|--------------|----------------|-----------------|
| ≤ 200k tokens | $2.00 | $12.00 |
| > 200k tokens | $4.00 | $18.00 |

### Gemini 3 Flash
| Context Size | Input (per 1M) | Output (per 1M) |
|--------------|----------------|-----------------|
| All sizes | $0.50 | $3.00 |

### Gemini 3 Pro Image
| Type | Cost |
|------|------|
| Text input | $2.00 per 1M tokens |
| 1K-2K image | ~$0.134 per image |
| 4K image | ~$0.24 per image |

## Rate Limits

Rate limits vary by tier:
- **Free tier**: Available through Google AI Studio with restrictions
- **Pay-as-you-go**: Higher limits with billing enabled
- **Enterprise (Vertex AI)**: Custom limits based on agreement

Check current limits in [Google AI Studio](https://aistudio.google.com/) or Vertex AI console.

## Error Handling

Common error codes:

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Invalid request (missing thought signature, bad params) | Check request format |
| 401 | Authentication failed | Verify API key |
| 429 | Rate limit exceeded | Implement backoff |
| 500 | Server error | Retry with backoff |

```python
from google.genai.errors import APIError

try:
    response = client.models.generate_content(
        model='gemini-3-pro-preview',
        contents='Hello'
    )
except APIError as e:
    print(f"Error {e.code}: {e.message}")
```

## References

- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [Thinking Documentation](https://ai.google.dev/gemini-api/docs/thinking)
- [Vertex AI Gemini 3 Pro](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro)
