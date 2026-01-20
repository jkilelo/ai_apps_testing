# Media Generation (Veo, Imagen, Flow)

Google's suite of generative media models for video, image, and audio creation.

## Veo (Video Generation)

### Available Models

| Model | Description | Pricing |
|-------|-------------|---------|
| `veo-3.1` | Latest, best quality | $0.40/second |
| `veo-3.1-fast` | Faster generation | $0.15/second |
| `veo-3` | Synchronized audio | Legacy |
| `veo-2` | Standard video | Legacy |

### Key Features

- **Native Audio**: Natural conversations, sound effects, ambient noise
- **4K Upscaling**: 1080p and 4K resolution support
- **Vertical Video**: Native support for social platforms (Jan 2026)
- **Reference Images**: Better character consistency with image inputs
- **Cinematic Control**: Understanding of cinematic styles

### Basic Video Generation

```python
from google import genai

client = genai.Client(api_key='YOUR_API_KEY')

response = client.models.generate_content(
    model='veo-3.1',
    contents='A serene lake at sunset with mountains in the background',
    config={
        'response_modalities': ['VIDEO'],
        'video_config': {
            'aspect_ratio': '16:9',
            'duration_seconds': 5
        }
    }
)

# Save video
with open('output.mp4', 'wb') as f:
    f.write(response.video_data)
```

### Veo 3 Audio Features (May 2025)

Veo 3 introduced synchronized audio generation:
- Dialogue matching lip movements
- Sound effects matching actions
- Ambient noise appropriate to scene

## Imagen 3 (Image Generation)

Google's highest quality image generation model.

### Capabilities

- Photorealistic image generation
- Superior detail and lighting
- Minimal artifacts
- Text rendering in images
- Style transfer

### Usage

```python
response = client.models.generate_content(
    model='imagen-3',
    contents='A professional headshot of a business executive',
    config={
        'response_modalities': ['IMAGE'],
        'image_config': {
            'aspect_ratio': '1:1',
            'output_format': 'png'
        }
    }
)
```

## Google Flow

AI filmmaking platform combining Veo, Imagen, and Gemini.

**Status:** Available on Google AI Pro and Ultra plans

### Key Features

| Feature | Description |
|---------|-------------|
| Camera Control | Change angles and views within scenes |
| Scene Builder | Edit, extend shots, direct scene flow |
| Asset Management | Import or create with Imagen |
| Natural Language | Describe vision in everyday language |

### Usage Limits

| Plan | Generations/Month |
|------|-------------------|
| AI Pro | 100 |
| AI Ultra | Higher (unspecified) |

### Recent Updates (October 2025)

- 275M+ videos generated since launch
- Veo 3.1 integration
- Audio across all features
- More precise editing capabilities

### Flow Workflow

1. **Describe** your vision in natural language
2. **Generate** initial video with Veo
3. **Edit** using scene builder
4. **Extend** shots as needed
5. **Add** custom assets with Imagen
6. **Export** final production

## Batch Processing for Media

Use batch API for high-volume generation:

```python
batch = client.batches.create(
    model='gemini-2.5-flash-image',  # Nano Banana
    requests=[
        {'prompt': 'Mountain landscape', 'custom_id': 'img-1'},
        {'prompt': 'Ocean sunset', 'custom_id': 'img-2'},
    ]
)
```

**Discount:** 50% off standard pricing

## Safety & Watermarking

### SynthID
All generated media includes invisible SynthID watermarks:
- Identifies AI-generated content
- Cannot be disabled
- Survives basic editing

### Content Filters
- Built-in safety filters
- Cannot generate harmful content
- Child safety protections always active

## Pricing Summary

| Service | Cost |
|---------|------|
| Veo 3.1 | $0.40/second |
| Veo 3.1 Fast | $0.15/second |
| Imagen 3 | Per-image pricing |
| Flow | Included in AI Pro/Ultra |

## Global AI Film Award

**Prize:** $1,000,000 USD
**Deadline:** January 2026

Requirements:
- Use Google AI tools for 70% of content
- Include Veo/Imagen/Gemini
- Submit to 1 Billion Followers Summit

## References

- [Veo Documentation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/veo-video-generation)
- [Veo 3.1 Announcement](https://developers.googleblog.com/introducing-veo-3-1-and-new-creative-capabilities-in-the-gemini-api/)
- [Flow Platform](https://labs.google/flow/about)
- [Imagen 3 on Vertex AI](https://cloud.google.com/blog/products/ai-machine-learning/introducing-veo-and-imagen-3-on-vertex-ai)
