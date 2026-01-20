# Image Generation with Gemini

Gemini provides native image generation capabilities through the "Nano Banana" models. This guide covers image generation, editing, and best practices.

## Available Models

| Model | Codename | Best For |
|-------|----------|----------|
| `gemini-2.5-flash-image` | Nano Banana | Fast, high-volume generation |
| `gemini-3-pro-image-preview` | Nano Banana Pro | Professional assets, highest quality |

## Gemini 3 Pro Image (Nano Banana Pro)

The most advanced image generation model with:
- 1K, 2K, and 4K resolution support
- Advanced text rendering in images
- Multi-image reference support
- Thinking process for complex prompts
- Google Search grounding for factual imagery

### Basic Image Generation

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='YOUR_API_KEY')

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents='Generate an image of a futuristic city at sunset with flying cars',
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)

# Access generated image
for part in response.candidates[0].content.parts:
    if part.inline_data:
        # Save image
        with open('generated_image.png', 'wb') as f:
            f.write(part.inline_data.data)
        print(f"Image saved (MIME: {part.inline_data.mime_type})")
    elif part.text:
        print(f"Description: {part.text}")
```

### Image Configuration

```python
response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents='Create a professional logo for a tech company called "NeuralFlow"',
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        image_generation_config=types.ImageGenerationConfig(
            aspect_ratio='1:1',      # Square for logo
            output_format='png',
            quality='high'
        )
    )
)
```

### Supported Aspect Ratios

| Ratio | Use Case |
|-------|----------|
| `1:1` | Logos, profile pictures, social media |
| `16:9` | Presentations, video thumbnails |
| `9:16` | Mobile, stories, vertical content |
| `4:3` | Standard photos, documents |
| `3:4` | Portrait orientation |

### Resolution Options

| Resolution | Token Cost | Cost per Image |
|------------|------------|----------------|
| 1K-2K | 1,120 tokens | ~$0.134 |
| 4K | 2,000 tokens | ~$0.24 |

## Text Rendering in Images

Gemini 3 Pro Image excels at generating legible text:

```python
response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents='''Create a restaurant menu with:
    - Header: "Le Petit Bistro"
    - Sections: Appetizers, Main Courses, Desserts
    - Include 3 items per section with prices
    - Elegant French cafe aesthetic''',
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)
```

**Best for text-heavy images:**
- Infographics
- Menus and signage
- Marketing materials
- Diagrams with labels
- Certificates and awards

## Image Editing

### Edit with Text Instructions

```python
from PIL import Image

# Load existing image
original_image = Image.open('photo.jpg')

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[
        original_image,
        'Change the sky to a dramatic sunset with orange and purple colors'
    ],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)
```

### Multi-Image Reference

Gemini 3 Pro can use up to 14 reference images:
- Up to 6 object images for high-fidelity reproduction
- Up to 5 human images for character consistency

```python
# Load reference images
product_image = Image.open('product.jpg')
style_image = Image.open('style_reference.jpg')

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[
        product_image,
        style_image,
        'Create a product advertisement featuring the product in the first image, using the artistic style from the second image'
    ],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)
```

### Character Consistency

```python
# Reference photos of a character
character_ref1 = Image.open('character_front.jpg')
character_ref2 = Image.open('character_side.jpg')

response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[
        character_ref1,
        character_ref2,
        'Generate an image of this same person sitting at a cafe, maintaining their appearance'
    ],
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)
```

## Grounding with Google Search

Generate images based on real-world facts:

```python
response = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents='Generate an accurate image of the Sagrada Familia cathedral in Barcelona',
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT'],
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    )
)
```

## Gemini 2.5 Flash Image (Nano Banana)

Faster and more cost-effective for high-volume generation:

```python
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='A cute cartoon cat wearing a top hat',
    config=types.GenerateContentConfig(
        response_modalities=['IMAGE', 'TEXT']
    )
)
```

### When to Use Flash vs Pro

| Use Case | Recommendation |
|----------|----------------|
| Prototyping | Flash |
| High-volume generation | Flash |
| Professional marketing assets | Pro |
| Text-heavy images | Pro |
| Maximum quality | Pro |
| Complex multi-reference | Pro |

## Thought Process in Image Generation

Gemini 3 Pro Image uses a "thinking" process:
1. Analyzes the prompt
2. Generates interim "thought images" to refine composition
3. Produces final high-quality output

This improves:
- Complex prompt interpretation
- Layout and composition
- Text placement
- Style consistency

## SynthID Watermarking

All generated images include SynthID watermarks - invisible digital watermarks that identify AI-generated content. This is automatic and cannot be disabled.

## Thought Signatures

**Important:** For image generation with Gemini 3, thought signatures are strictly validated. Missing signatures result in a 400 error.

The SDK handles this automatically when using standard patterns. For custom implementations, ensure proper signature handling in multi-turn interactions.

## Best Practices

### 1. Write Detailed Prompts

```python
# Less effective
contents = 'A mountain landscape'

# More effective
contents = '''A majestic mountain landscape at golden hour:
- Snow-capped peaks reflecting warm sunlight
- Alpine meadow with wildflowers in foreground
- Crystal clear lake creating mirror reflection
- Dramatic clouds with pink and orange hues
- Photorealistic style with high detail'''
```

### 2. Specify Style and Mood

```python
contents = '''Portrait of a scientist in a laboratory
Style: Classic oil painting, reminiscent of Rembrandt
Mood: Contemplative, intellectual
Lighting: Dramatic chiaroscuro
Details: Period-appropriate clothing, scientific instruments'''
```

### 3. Use Negative Prompts Implicitly

```python
contents = '''Modern minimalist living room interior
Clean lines, uncluttered space
Natural light from large windows
No people, no pets
Simple furniture arrangement'''
```

### 4. Iterate with Edits

```python
# Generate initial image
response1 = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents='A cozy reading nook with built-in bookshelves'
)

# Save and refine
# ... save image ...
nook_image = Image.open('nook.png')

response2 = client.models.generate_content(
    model='gemini-3-pro-image-preview',
    contents=[
        nook_image,
        'Add a cat sleeping on the chair and warm afternoon light'
    ]
)
```

## Pricing

### Gemini 3 Pro Image
| Component | Cost |
|-----------|------|
| Text input | $2.00 per 1M tokens |
| 1K-2K image output | ~$0.134 per image |
| 4K image output | ~$0.24 per image |

### Gemini 2.5 Flash Image
Lower cost tier for high-volume use cases.

## Limitations

- Maximum 14 reference images
- No real-time video generation
- SynthID watermarks always applied
- Some content restrictions apply
- Cannot combine with custom function calling in Gemini 3

## Example: Complete Workflow

```python
from google import genai
from google.genai import types
from PIL import Image
import io

client = genai.Client(api_key='YOUR_API_KEY')

def generate_and_save(prompt: str, filename: str, model: str = 'gemini-3-pro-image-preview'):
    """Generate an image and save to file."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['IMAGE', 'TEXT']
        )
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data:
            image_data = part.inline_data.data
            image = Image.open(io.BytesIO(image_data))
            image.save(filename)
            print(f"Saved: {filename}")
            return image
        elif part.text:
            print(f"Model comment: {part.text}")

    return None

# Generate a series of related images
prompts = [
    ('hero_image.png', 'Modern tech startup office, open floor plan, natural light'),
    ('team_photo.png', 'Diverse team of developers collaborating at whiteboard'),
    ('product_shot.png', 'Sleek mobile app interface on smartphone, floating design')
]

for filename, prompt in prompts:
    generate_and_save(prompt, filename)
```

## References

- [Image Generation Guide](https://ai.google.dev/gemini-api/docs/image-generation)
- [Gemini 3 Pro Image](https://deepmind.google/models/gemini-image/pro/)
- [Vertex AI Image Generation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro-image)
