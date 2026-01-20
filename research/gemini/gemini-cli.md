# Gemini CLI

Gemini CLI is an open-source AI agent that brings the power of Gemini directly into your terminal. Released in June 2025 under the Apache 2.0 license.

**Repository:** https://github.com/google-gemini/gemini-cli

## Installation

```bash
# npm
npm install -g @anthropic-ai/gemini-cli

# or use directly
npx @anthropic-ai/gemini-cli
```

## Free Tier

Gemini CLI offers the **industry's largest free usage allowance**:
- 60 model requests per minute
- 1,000 model requests per day
- Access to Gemini 2.5 Pro with 1M token context window

To use free: Login with a personal Google account to get a free Gemini Code Assist license.

## Key Features

### ReAct Loop Architecture
Gemini CLI uses a reason-and-act (ReAct) loop with built-in tools and MCP servers to complete complex tasks like:
- Fixing bugs
- Creating new features
- Improving test coverage
- Content generation
- Deep research
- Task management

### Model Support
- **Gemini 3 Flash** (default as of Dec 2025): 78% on SWE-bench Verified
- **Gemini 3 Pro**: Advanced reasoning and tool usage
- **Gemini 2.5 Pro**: 1M token context window

### MCP Integration
Gemini CLI supports local and remote MCP servers for extended capabilities:
- Connect to external tools and data sources
- Custom MCP server integration
- Full MCP protocol support

## GEMINI.md Configuration

Similar to CLAUDE.md, Gemini CLI uses `GEMINI.md` for persistent configuration:

```markdown
# Project Context
This is a React TypeScript project...

# Build Commands
- `npm run build` - Production build
- `npm test` - Run tests

# Conventions
- Use functional components
- Prefer TypeScript strict mode
```

### Location
- **Project root**: `./GEMINI.md`
- **User-level**: `~/.gemini/GEMINI.md`

## Agent Mode in VS Code

Gemini CLI powers **Agent Mode** in Gemini Code Assist for VS Code:
- Multiple file edits
- Full project context
- Built-in tools
- MCP ecosystem integration

## Basic Usage

```bash
# Start interactive session
gemini

# With initial prompt
gemini "explain this codebase"

# Specific task
gemini "fix the failing tests in src/utils"
```

## Comparison with Claude Code

| Feature | Gemini CLI | Claude Code |
|---------|------------|-------------|
| Free tier | 1,000 req/day | Limited |
| Context window | 1M tokens | 200k tokens |
| MCP support | ✓ | ✓ |
| Open source | ✓ (Apache 2.0) | ✗ |
| Agent mode | ✓ | ✓ |

## Latest Updates (January 2026)

- Gemini 3 Flash now available (78% SWE-bench)
- Improved agentic coding capabilities
- Enhanced tool usage
- Better natural-language coding support

## References

- [Gemini CLI Announcement](https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/)
- [GitHub Repository](https://github.com/google-gemini/gemini-cli)
- [Gemini Code Assist Docs](https://developers.google.com/gemini-code-assist/docs/gemini-cli)
