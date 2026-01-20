# Gemini 3 Overview

Gemini 3, released on November 18, 2025, is Google's most advanced AI model to date. It combines state-of-the-art reasoning capabilities with advanced multimodal understanding and agentic functionality.

## Model Variants

### Gemini 3 Pro (`gemini-3-pro-preview`)
The flagship model optimized for complex tasks requiring broad knowledge and advanced reasoning across modalities.

**Specifications:**
- Input context: 1 million tokens
- Output limit: 64,000 tokens
- Knowledge cutoff: January 2025
- Pricing: $2/$12 per 1M tokens (input/output) for ≤200k context
- Pricing: $4/$18 per 1M tokens (input/output) for >200k context

### Gemini 3 Flash (`gemini-3-flash-preview`)
Delivers Pro-level intelligence at Flash speed and pricing. The next generation's Flash model surpasses the previous generation's Pro model.

**Specifications:**
- Input context: 1 million tokens
- Output limit: 64,000 tokens
- Knowledge cutoff: January 2025
- Pricing: $0.50/$3 per 1M tokens (input/output)

### Gemini 3 Pro Image (`gemini-3-pro-image-preview`)
Also known as "Nano Banana Pro" - the highest quality native image generation model.

**Specifications:**
- Input context: 65,000 tokens
- Output limit: 32,000 tokens
- Knowledge cutoff: January 2025
- Pricing: $2 per 1M text tokens, ~$0.134 per image (1K-2K), ~$0.24 per image (4K)

## Benchmarks

### Gemini 3 Pro Performance

| Benchmark | Score |
|-----------|-------|
| LMArena Elo | 1501 (top leaderboard) |
| GPQA Diamond | 91.9% |
| SWE-bench Verified | 76.2% |
| Humanity's Last Exam | 37.5% (standard) |

### Gemini 3 Deep Think Performance

| Benchmark | Score |
|-----------|-------|
| Humanity's Last Exam | 41.0% (without tools) |
| GPQA Diamond | 93.8% |
| ARC-AGI-2 | 45.1% (with code execution) |

## Core Capabilities

### 1. Advanced Reasoning
Gemini 3 is built to grasp depth and nuance - perceiving subtle clues in creative ideas and analyzing overlapping layers of complex problems. The "thinking" process enables step-by-step reasoning before generating responses.

### 2. Multimodal Understanding
- **Text**: Natural language processing and generation
- **Images**: Visual understanding, analysis, and generation
- **Video**: Temporal understanding and analysis
- **Audio**: Speech recognition and understanding
- **Code**: Code generation, analysis, and debugging

### 3. Agentic Capabilities
- Exceptional instruction following
- Improved tool use and function calling
- Autonomous task completion
- Multi-step problem solving

### 4. Deep Think Mode
An enhanced reasoning mode for tackling complex math, science, and logic problems. Available to Google AI Ultra subscribers in the Gemini app.

**When to use Deep Think:**
- Complex mathematical proofs
- Scientific reasoning problems
- Logic puzzles and formal verification
- Problems requiring extended chain-of-thought

### 5. Native Image Generation
Gemini 3 Pro Image can generate and edit high-quality images with:
- 1K, 2K, and 4K resolution support
- Advanced text rendering in images
- Multi-image reference support (up to 14 images)
- Character consistency across generations

## Grounding Capabilities

Gemini 3 supports multiple grounding sources:

| Tool | Description |
|------|-------------|
| Google Search | Real-time web search for current information |
| URL Context | Extract and use content from specific URLs |
| File Search | Search uploaded documents and files |
| Code Execution | Run Python code in a sandboxed environment |

## Key Improvements Over Gemini 2.x

1. **Reasoning Depth**: Significantly improved complex reasoning capabilities
2. **Instruction Following**: Better adherence to detailed instructions
3. **Tool Use**: More reliable function calling and tool integration
4. **Agentic Coding**: Enhanced autonomous coding capabilities
5. **Multimodal Integration**: Seamless handling of mixed-modality inputs/outputs

## Availability

- **Google AI Studio**: Free tier with rate limits, full access with API key
- **Vertex AI**: Enterprise deployment with additional features
- **Gemini App**: Consumer access including Deep Think mode
- **Google Search**: Powers AI Mode and AI Overviews
- **Gmail**: Powers new AI features for email composition

## Limitations

- No image segmentation support
- Maps grounding not yet available
- Computer Use feature unavailable
- Cannot combine built-in tools with custom function calling in same request

## References

- [Gemini 3 Announcement](https://blog.google/products/gemini/gemini-3/)
- [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3)
- [Google DeepMind Models](https://deepmind.google/models/gemini/)
