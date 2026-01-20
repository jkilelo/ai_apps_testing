# Google GenAI SDK Advanced Features

Advanced usage patterns for the `google-genai` SDK including async operations, streaming, caching, and file management.

## Async Support

The SDK provides full async support via the `client.aio` namespace.

### Setup

```bash
pip install google-genai[aiohttp]
```

### Basic Async Usage

```python
import asyncio
from google import genai

async def main():
    client = genai.Client(api_key='YOUR_API_KEY')

    response = await client.aio.models.generate_content(
        model='gemini-3-flash-preview',
        contents='Explain async programming'
    )
    print(response.text)

asyncio.run(main())
```

### Async Context Manager

```python
async def main():
    async with genai.Client(api_key='YOUR_API_KEY').aio as aclient:
        response = await aclient.models.generate_content(
            model='gemini-3-flash-preview',
            contents='Hello!'
        )
        print(response.text)
```

### Async Streaming

```python
async def stream_response():
    client = genai.Client(api_key='YOUR_API_KEY')

    async for chunk in await client.aio.models.generate_content_stream(
        model='gemini-3-flash-preview',
        contents='Write a detailed explanation of machine learning'
    ):
        print(chunk.text, end='', flush=True)

asyncio.run(stream_response())
```

### Async Chat

```python
async def chat_session():
    client = genai.Client(api_key='YOUR_API_KEY')

    chat = client.aio.chats.create(model='gemini-3-flash-preview')

    # Send messages
    response = await chat.send_message('What is Python?')
    print(response.text)

    # Streaming chat
    async for chunk in await chat.send_message_stream('Tell me more'):
        print(chunk.text, end='', flush=True)

asyncio.run(chat_session())
```

### Concurrent Requests

```python
async def batch_process():
    client = genai.Client(api_key='YOUR_API_KEY')

    prompts = [
        'Summarize machine learning',
        'Explain neural networks',
        'What is deep learning?'
    ]

    tasks = [
        client.aio.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        for prompt in prompts
    ]

    responses = await asyncio.gather(*tasks)

    for prompt, response in zip(prompts, responses):
        print(f"Q: {prompt}")
        print(f"A: {response.text[:100]}...")
        print()

asyncio.run(batch_process())
```

## Streaming

Streaming reduces time-to-first-token for better user experience.

### Synchronous Streaming

```python
client = genai.Client(api_key='YOUR_API_KEY')

for chunk in client.models.generate_content_stream(
    model='gemini-3-flash-preview',
    contents='Write a poem about technology'
):
    print(chunk.text, end='', flush=True)
print()  # Final newline
```

### Streaming with Metadata

```python
for chunk in client.models.generate_content_stream(
    model='gemini-3-flash-preview',
    contents='Explain quantum computing'
):
    # Access chunk content
    if chunk.text:
        print(chunk.text, end='')

    # Check for finish reason
    if chunk.candidates and chunk.candidates[0].finish_reason:
        print(f"\n[Finished: {chunk.candidates[0].finish_reason}]")
```

## File Management

Upload and manage files for use in prompts. Files are only supported with the Gemini Developer API.

### Upload Files

```python
# Upload a file
file = client.files.upload(file='document.pdf')
print(f"Uploaded: {file.name}")
print(f"URI: {file.uri}")
print(f"State: {file.state}")

# Use in prompt
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[
        file,
        'Summarize this document'
    ]
)
```

### File Operations

```python
# List files
files = client.files.list()
for f in files:
    print(f"{f.name}: {f.display_name}")

# Get file info
file_info = client.files.get(name='files/abc123')
print(f"Size: {file_info.size_bytes} bytes")
print(f"MIME type: {file_info.mime_type}")

# Delete file
client.files.delete(name='files/abc123')
```

### Large File Handling

For files larger than inline limits, always upload first:

```python
# Upload large video
video_file = client.files.upload(file='large_video.mp4')

# Wait for processing (videos need time to process)
import time
while video_file.state == 'PROCESSING':
    time.sleep(5)
    video_file = client.files.get(name=video_file.name)

if video_file.state == 'ACTIVE':
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[
            video_file,
            'Describe the key moments in this video'
        ]
    )
    print(response.text)
```

## Caching

Reduce costs when repeatedly using the same large context.

### Create a Cache

```python
from google.genai import types

# Cache large document content
cache = client.caches.create(
    model='gemini-3-flash-preview',
    config=types.CreateCachedContentConfig(
        contents=[
            'This is a very long document that will be used repeatedly...',
            # Or include uploaded files
        ],
        system_instruction='You are an expert analyst of this document.',
        ttl='3600s'  # Cache for 1 hour
    )
)

print(f"Cache name: {cache.name}")
print(f"Expires: {cache.expire_time}")
```

### Use Cached Content

```python
# Generate with cached context
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='What are the main themes?',
    config=types.GenerateContentConfig(
        cached_content=cache.name
    )
)
print(response.text)
```

### Cache with Chat History

```python
# Create chat and have conversation
chat = client.chats.create(model='gemini-3-flash-preview')
chat.send_message('Let me tell you about a complex topic...')
chat.send_message('Here are more details...')

# Cache the conversation history
cache = client.caches.create(
    model='gemini-3-flash-preview',
    config=types.CreateCachedContentConfig(
        contents=chat.get_history(),
        system_instruction='Continue this conversation helpfully.'
    )
)

# Start new chat with cached history
new_chat = client.chats.create(
    model='gemini-3-flash-preview',
    config=types.GenerateContentConfig(
        cached_content=cache.name
    )
)

response = new_chat.send_message('Based on what we discussed, what should I do?')
```

### Manage Caches

```python
# List caches
caches = client.caches.list()
for c in caches:
    print(f"{c.name}: expires {c.expire_time}")

# Get cache info
cache_info = client.caches.get(name='cachedContents/abc123')

# Update TTL
updated_cache = client.caches.update(
    name='cachedContents/abc123',
    config=types.UpdateCachedContentConfig(
        ttl='7200s'  # Extend to 2 hours
    )
)

# Delete cache
client.caches.delete(name='cachedContents/abc123')
```

## Embeddings

Generate vector embeddings for semantic search and RAG.

```python
# Single embedding
response = client.models.embed_content(
    model='text-embedding-004',
    contents='This is a sample text to embed'
)
embedding = response.embeddings[0].values
print(f"Embedding dimension: {len(embedding)}")

# Batch embeddings
texts = ['First document', 'Second document', 'Third document']
response = client.models.embed_content(
    model='text-embedding-004',
    contents=texts
)
for i, emb in enumerate(response.embeddings):
    print(f"Text {i}: {len(emb.values)} dimensions")
```

## Batch Processing

For high-volume processing:

```python
from google.genai import types

# Create batch job
batch = client.batches.create(
    model='gemini-3-flash-preview',
    src='gs://your-bucket/input.jsonl',
    dest='gs://your-bucket/output/',
    config=types.CreateBatchJobConfig(
        display_name='my-batch-job'
    )
)

print(f"Batch job: {batch.name}")
print(f"State: {batch.state}")

# Check status
batch_info = client.batches.get(name=batch.name)
print(f"Progress: {batch_info.state}")
```

## Model Tuning

Fine-tune models on your data:

```python
from google.genai import types

# Create tuning job
tuning_job = client.tunings.create(
    base_model='gemini-3-flash-preview',
    training_data='gs://your-bucket/training.jsonl',
    config=types.CreateTuningJobConfig(
        tuned_model_display_name='my-custom-model',
        epoch_count=3,
        learning_rate=0.001
    )
)

print(f"Tuning job: {tuning_job.name}")

# Check status
job_info = client.tunings.get(name=tuning_job.name)
print(f"State: {job_info.state}")

# Use tuned model
if job_info.state == 'SUCCEEDED':
    response = client.models.generate_content(
        model=job_info.tuned_model.name,
        contents='Your prompt here'
    )
```

## SDK Modules Reference

| Module | Purpose |
|--------|---------|
| `client.models` | Content generation, embeddings |
| `client.chats` | Multi-turn conversations |
| `client.files` | File upload/management |
| `client.caches` | Prompt caching |
| `client.batches` | Batch processing |
| `client.tunings` | Model fine-tuning |
| `client.aio.*` | Async versions of all above |

## Best Practices

1. **Use streaming** for long responses to improve perceived latency
2. **Cache large contexts** that are reused across multiple requests
3. **Upload files** instead of sending inline for documents >10MB
4. **Use async** when making multiple concurrent API calls
5. **Handle rate limits** with exponential backoff
6. **Monitor token usage** to optimize costs

## References

- [SDK Documentation](https://googleapis.github.io/python-genai/)
- [Caching Guide](https://ai.google.dev/gemini-api/docs/caching)
- [File API](https://ai.google.dev/gemini-api/docs/files)
