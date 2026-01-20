# Claude Voice & Real-Time Features

Voice mode and real-time streaming capabilities for Claude.

## Voice Mode

**Released:** May 27, 2025
**Status:** Beta (English, expanding)

### Overview

Voice mode enables complete spoken conversations with Claude through the mobile app and API.

### Modes

| Mode | Description |
|------|-------------|
| **Push-to-talk** | Press to speak |
| **Continuous Listening** | Hands-free with "Hey Claude" wake phrase |

### Features

- Real-time voice conversations
- Live transcripts during conversation
- Session summaries after completion
- 5 voice styles with unique tones
- Up to 30-minute continuous sessions

### Default Model

Claude Sonnet 4 powers voice mode by default.

### Language Support

| Capability | Languages |
|------------|-----------|
| Input detection | 38 languages (automatic) |
| Neural TTS voices | 14 voices |
| Code-switching | Supported (mid-sentence language changes) |

## Voice API

### WebSocket Streaming

```python
import websockets
import json

async def voice_session():
    uri = "wss://api.anthropic.com/v1/audio/stream"

    async with websockets.connect(uri, extra_headers={
        "x-api-key": API_KEY,
        "anthropic-beta": "voice-2025-05-27"
    }) as ws:
        # Send PCM audio
        await ws.send(audio_chunk)

        # Receive response
        async for message in ws:
            data = json.loads(message)
            if data.get("type") == "audio":
                play_audio(data["audio"])
            elif data.get("type") == "transcript":
                print(data["text"])
```

### API Endpoint

```
POST /v1/audio/stream
```

Uses WebSocket-based PCM audio streaming.

## Performance Comparison

### Claude Voice vs OpenAI Realtime

| Metric | Claude Voice | OpenAI Realtime |
|--------|--------------|-----------------|
| Time-to-first-phoneme | 300-360ms | 230-290ms |
| Prosody/Expressiveness | Higher | Standard |
| Turn-taking speed | Good | Slightly faster |

**Summary:** OpenAI is slightly faster; Claude sounds warmer and more expressive.

## Integrations

### Pro Plan Features

For Pro users and above:
- Integration with Google Docs, Drive, Calendar
- Real-time web search in conversations
- Personal information source access

### Third-Party Integrations

| Service | Integration |
|---------|-------------|
| Amazon Alexa+ | Voice AI powered by Claude |
| Otter AI | Transcription services |

## Mobile App Features

### v2.4 Updates

- Continuous Conversation Mode
- "Hey Claude" wake phrase
- Interrupt responses anytime
- Post-session summaries

### Requirements

- Claude mobile app
- Pro, Team, or Enterprise subscription for full features

## Building Voice Applications

### Using Third-Party TTS

```python
import anthropic
from picovoice import Orca  # Example TTS

client = anthropic.Anthropic()

# Get text response from Claude
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=500,
    messages=[{"role": "user", "content": transcribed_speech}]
)

# Convert to speech with TTS
tts = Orca(access_key="...")
audio = tts.synthesize(response.content[0].text)
play(audio)
```

### Complete Voice Assistant

```python
# 1. Speech-to-text (user input)
text = transcribe(audio_input)

# 2. Claude processing
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": text}]
)

# 3. Text-to-speech (response)
audio_output = synthesize(response.content[0].text)
play(audio_output)
```

## Streaming Text Responses

For text-based real-time streaming:

```python
with client.messages.stream(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Best Practices

1. **Use streaming** for all voice applications
2. **Handle interrupts** - allow users to stop responses
3. **Provide transcripts** for accessibility
4. **Consider latency** in UI design
5. **Test multiple voices** for your use case

## Limitations

- Voice mode currently in beta
- English primary, other languages expanding
- 30-minute max session length
- API voice features require beta access

## References

- [Voice Mode Announcement](https://techcrunch.com/2025/05/27/anthropic-launches-a-voice-mode-for-claude/)
- [Streaming Documentation](https://platform.claude.com/docs/en/api/streaming)
- [Mobile App](https://claude.ai/mobile)
