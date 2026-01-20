# Citations & Files API

Document grounding and file management capabilities for Claude.

## Citations API

**Released:** June 30, 2025
**Status:** Generally Available

Citations enables Claude to ground responses in source documents with precise references.

### Supported Models

- Claude Opus 4/4.5
- Claude Sonnet 4/4.5
- Claude Sonnet 3.7
- Claude Sonnet 3.5v2

### Availability

- Anthropic API ✓
- Amazon Bedrock ✓
- Google Vertex AI ✓

### Basic Usage

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_base64
                },
                "citations": {"enabled": True}
            },
            {
                "type": "text",
                "text": "Summarize the key findings from this document"
            }
        ]
    }]
)

# Response includes citation blocks
for block in response.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "citation":
        print(f"Source: {block.cited_text}")
        print(f"Document: {block.document_index}")
```

### How It Works

1. Documents are chunked into sentences
2. Sentences passed with query to model
3. Claude references specific passages
4. Response includes citation blocks with source locations

### Benefits Over Custom Solutions

| Metric | Improvement |
|--------|-------------|
| Recall Accuracy | +15% |
| Source Hallucinations | 0% (vs 10% prompt-based) |
| References per Response | +20% |

### Cost Savings

`cited_text` does **not** count toward output tokens, potentially reducing costs vs prompt-based citation approaches.

### Custom Chunking

You can pre-chunk documents for more control:

```python
{
    "type": "document",
    "source": {"type": "text", "text": "..."},
    "citations": {
        "enabled": True,
        "chunks": [
            {"text": "First paragraph...", "id": "p1"},
            {"text": "Second paragraph...", "id": "p2"}
        ]
    }
}
```

### Limitations

**Cannot combine with Structured Outputs.** Enabling citations with `output_format` returns 400 error due to incompatible response structures.

## Files API

**Released:** April 14, 2025
**Status:** Public Beta

Upload and manage files for use across API requests.

### Beta Header

```
anthropic-beta: files-api-2025-04-14
```

### Supported File Types

| Type | Extensions |
|------|------------|
| Documents | PDF, DOCX, TXT, MD |
| Data | CSV, Excel, JSON |
| Images | PNG, JPG, GIF, WebP |

### Limits

| Parameter | Limit |
|-----------|-------|
| File size | 350 MB |
| Retention | 0-365 days (configurable) |

### Upload File

```python
import anthropic

client = anthropic.Anthropic()

# Upload file
file = client.files.create(
    file=open("document.pdf", "rb"),
    purpose="messages"
)

print(f"File ID: {file.id}")
print(f"Filename: {file.filename}")
```

### Use in Messages

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "file",
                    "file_id": file.id
                },
                "title": "Annual Report",
                "context": "Company financial data",
                "citations": {"enabled": True}
            },
            {"type": "text", "text": "What was the revenue growth?"}
        ]
    }]
)
```

### File Operations

```python
# List files
files = client.files.list()

# Get file info
file_info = client.files.retrieve(file_id="file-abc123")

# Delete file
client.files.delete(file_id="file-abc123")
```

### Download Limitations

- **Cannot download** user-uploaded files
- **Can download** files created by code execution or skills

### Workspace Scope

Files are scoped to the API key's workspace. Any API key in the same workspace can access files created by other keys.

## PDF Processing

### How It Works

1. Each page converted to image
2. Text extracted alongside images
3. Page images and text interleaved
4. Enables visual + textual analysis

### Capabilities

- Text extraction
- Chart/graph analysis
- Table understanding
- Visual content interpretation
- Layout-aware processing

### Limits

| Parameter | Limit |
|-----------|-------|
| File size | 32 MB |
| Page count | 100 pages |

### Evolution

| Date | Feature |
|------|---------|
| Late 2024 | Text-only extraction |
| Feb 2025 | Full multimodal (rasterized pages + text) |
| May 2025 | URL source blocks for web streaming |

### Use Cases

- Financial analysis (annual reports, charts)
- Legal document summarization
- Technical documentation Q&A
- Research paper analysis

## References

- [Citations Documentation](https://platform.claude.com/docs/en/build-with-claude/citations)
- [Files API](https://platform.claude.com/docs/en/build-with-claude/files)
- [PDF Support](https://docs.claude.com/en/docs/build-with-claude/pdf-support)
- [Citations Announcement](https://claude.com/blog/introducing-citations-api)
