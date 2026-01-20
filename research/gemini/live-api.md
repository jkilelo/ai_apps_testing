# Gemini Live API

Real-time, low-latency voice and video interactions with Gemini models.

**Status:** Generally Available on Vertex AI

## Overview

The Live API enables continuous streams of audio, video, or text to deliver immediate, human-like spoken responses. It creates natural conversational experiences through WebSocket connections.

## Key Capabilities

| Feature | Description |
|---------|-------------|
| **Multimodality** | See, hear, and speak |
| **Low-latency** | Real-time responses |
| **Session Memory** | Retains context within session |
| **Barge-in** | Users can interrupt anytime |
| **Affective Dialog** | Adapts tone to user's emotion |

## Supported Languages

24 languages with high audio quality and natural speech.

## Latest Model

```
gemini-2.5-flash-native-audio-preview-12-2025
```

**Features:**
- Dynamic thinking enabled by default
- Natural, realistic speech
- Improved multilingual performance
- Emotion-aware dialogue
- Proactive audio (intelligent response timing)

## Basic Implementation

### WebSocket Connection

```python
import asyncio
import websockets
import json

async def live_session():
    uri = "wss://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:streamGenerateContent"

    async with websockets.connect(uri) as ws:
        # Send audio chunk
        await ws.send(json.dumps({
            "audio": {
                "data": audio_base64,
                "mimeType": "audio/pcm"
            }
        }))

        # Receive response
        async for message in ws:
            response = json.loads(message)
            if "audio" in response:
                play_audio(response["audio"])

asyncio.run(live_session())
```

### SDK Usage

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='YOUR_API_KEY')

# Create live session
session = client.live.create_session(
    model='gemini-2.5-flash-native-audio',
    config=types.LiveConfig(
        voice='Kore',  # Voice style
        language='en-US',
        enable_affective_dialog=True
    )
)

# Stream audio
async for response in session.stream(audio_input):
    if response.audio:
        play(response.audio)
    if response.text:
        print(response.text)  # Transcript
```

## Audio Configuration

### Input Formats
- PCM audio (recommended)
- 1 sample per second for video frames

### Output
- Natural text-to-speech
- Audio transcriptions available

### Voice Styles
Multiple voice options with unique tones and characteristics.

## Video Streaming

```python
session = client.live.create_session(
    model='gemini-2.5-flash-native-audio',
    config=types.LiveConfig(
        enable_video=True,
        video_fps=1  # 1 frame per second
    )
)

# Stream video frames
for frame in video_frames:
    await session.send_video(frame)
```

**Limitations:**
- 1 FPS video processing
- Not suitable for fast-changing video (sports, etc.)

## Tool Integration

Live API supports function calling:

```python
@tool
def get_stock_price(symbol: str) -> str:
    return f"${get_price(symbol)}"

session = client.live.create_session(
    model='gemini-2.5-flash-native-audio',
    tools=[get_stock_price],
    config=types.LiveConfig(
        tool_config={'mode': 'auto'}
    )
)
```

## Session Limits

| Parameter | Limit |
|-----------|-------|
| Max session length | 10 minutes (default) |
| Video FPS | 1 frame per second |
| Audio quality | High fidelity |

## Use Cases

### E-commerce & Retail
- Shopping assistants
- Customer support agents

### Gaming
- Interactive NPCs
- In-game help
- Real-time translation

### Healthcare
- Patient support companions
- Health education

### Financial Services
- AI wealth advisors
- Investment guidance

### Next-Gen Interfaces
- Robotics
- Smart glasses
- Vehicle assistants

## Architecture Patterns

### Server-to-Server
```
Client → Your Server → Live API → Gemini
         (WebSocket)   (WebSocket)
```

### Direct Client
```
Client → Live API → Gemini
      (WebSocket)
```

## Pricing

Live API pricing based on:
- Audio input tokens
- Audio output tokens
- Video frame tokens (if enabled)

See current pricing at [Google AI pricing](https://ai.google.dev/pricing).

## Firebase Integration

```javascript
import { initializeApp } from 'firebase/app';
import { getLiveSession } from 'firebase/ai-logic';

const session = await getLiveSession({
    model: 'gemini-2.5-flash-native-audio'
});

session.onMessage((message) => {
    if (message.audio) playAudio(message.audio);
});

session.sendAudio(audioChunk);
```

## References

- [Live API Overview](https://ai.google.dev/gemini-api/docs/live)
- [Live API Guide](https://ai.google.dev/gemini-api/docs/live-guide)
- [Vertex AI Live API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api)
- [Native Audio Blog Post](https://cloud.google.com/blog/topics/developers-practitioners/how-to-use-gemini-live-api-native-audio-in-vertex-ai)
