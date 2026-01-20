# Claude Code

Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster through natural language commands.

**Documentation:** https://code.claude.com/docs

## Installation

### macOS / Linux
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Homebrew (macOS/Linux)
```bash
brew install --cask claude-code
```

### Windows
```powershell
irm https://claude.ai/install.ps1 | iex
```

### WinGet (Windows)
```bash
winget install Anthropic.ClaudeCode
```

**Requirements:** Node.js 18+

## Basic Usage

```bash
# Navigate to your project
cd your-project

# Start Claude Code
claude

# Or with a specific prompt
claude "explain this codebase"
```

## Key Features

### Agentic Coding
- Understands entire codebases
- Executes routine tasks autonomously
- Explains complex code
- Handles git workflows

### Multi-Interface Support
- **Terminal CLI**: Primary interface
- **VS Code Extension**: Native IDE integration
- **GitHub**: Tag @claude in issues/PRs

### Latest Features (2025-2026)
- **Subagents**: Delegate specialized tasks (e.g., backend API while main agent builds frontend)
- **Hooks**: Automatically trigger actions at specific points
- **Background tasks**: Keep long-running processes active
- **Checkpoints**: Save progress and rollback to previous states
- **Context editing**: Better control over conversation context
- **Memory tool**: Persistent memory across sessions
- **Searchable prompt history**: Ctrl+R to reuse/edit prompts

## CLAUDE.md Configuration

CLAUDE.md is a special file that Claude automatically reads for project context.

### Location
- **Root**: `./CLAUDE.md` - Main project context
- **Subdirectories**: `./src/CLAUDE.md` - Additional context (appends, doesn't overwrite)
- **User-level**: `~/.claude/CLAUDE.md` - Personal preferences

### Contents
```markdown
# Project Overview
This is a React TypeScript application for...

# Architecture
- Frontend: React 18 with TypeScript
- State: Redux Toolkit
- API: REST with axios

# Conventions
- Use functional components with hooks
- Prefer named exports
- Tests use Jest and React Testing Library

# Commands
- Build: `npm run build`
- Test: `npm test`
- Lint: `npm run lint`

# Important Files
- src/App.tsx - Main entry point
- src/store/ - Redux store configuration
```

### Best Practices
- Keep semantic info (architecture, conventions, rules)
- Include absolute info (commands, directory structure)
- Update as project evolves
- Use for static knowledge that rarely changes

## Subagents

Subagents are isolated Claude instances that work on tasks independently.

### Creating Subagents

#### Via Slash Command
```
/agents
```

#### Manual Creation
Create `.claude/agents/my-agent.md`:

```markdown
---
name: Backend Developer
description: Specializes in Node.js backend development
tools:
  - Read
  - Write
  - Bash
  - Grep
---

You are an expert Node.js backend developer.
Focus on:
- Express.js API design
- Database schema design
- Authentication patterns

Always write tests for new endpoints.
```

### User-Level Subagents
Save to `~/.claude/agents/` for availability across all projects.

### When to Use Subagents
- Parallel execution of independent tasks
- Isolating heavy computational work
- Preventing context pollution
- Specialized deep dives (security audit, performance analysis)

## Hooks

Hooks trigger custom logic before or after Claude's actions.

### Configuration Location
- **Project**: `.claude/settings.json`
- **User**: `~/.claude/settings.json`

### Hook Events

| Event | Description |
|-------|-------------|
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool execution |
| `Stop` | When Claude finishes responding |
| `SubagentStop` | When a subagent finishes |
| `SessionStart` | When session starts/resumes |
| `SessionEnd` | When session ends |

### Hook Types

#### Command Hooks (Bash)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/validate-command.sh"
          }
        ]
      }
    ]
  }
}
```

#### Prompt Hooks (LLM-based)
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the changes for security issues"
          }
        ]
      }
    ]
  }
}
```

### Hook Exit Codes
| Code | Effect |
|------|--------|
| 0 | Allow operation |
| 2 | Block operation and return error message |

### Example: Block Dangerous Commands
```bash
#!/bin/bash
# validate-command.sh
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if [[ "$COMMAND" == *"rm -rf"* ]] || [[ "$COMMAND" == *"sudo"* ]]; then
  echo "Blocked: Dangerous command pattern detected"
  exit 2
fi
exit 0
```

## Skills

Skills are organized folders of instructions and resources that agents can load dynamically.

### Structure
```
.claude/skills/
├── code-review/
│   ├── SKILL.md
│   └── review-checklist.md
├── deployment/
│   ├── SKILL.md
│   └── deploy.sh
```

### SKILL.md Format
```markdown
---
name: Code Review
description: Comprehensive code review assistant
triggers:
  - "review"
  - "code review"
---

# Code Review Skill

When reviewing code:
1. Check for security vulnerabilities
2. Verify error handling
3. Assess performance implications
4. Review test coverage
```

### When to Use Skills
- Task-specific knowledge
- Dynamic capability loading
- Reusable workflows

## Custom Commands

Create custom slash commands in `.claude/commands/`.

### Example: `/deploy` Command
`.claude/commands/deploy.md`:
```markdown
---
name: deploy
description: Deploy the application
allowed_tools:
  - Bash
  - Read
---

Deploy the application:
1. Run tests
2. Build the project
3. Deploy to staging
4. Run smoke tests
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `claude` | Start interactive session |
| `claude "prompt"` | Start with prompt |
| `claude --help` | Show help |
| `/bug` | Report a bug |
| `/agents` | Manage subagents |
| `/commands` | List custom commands |
| `Ctrl+R` | Search prompt history |

## Best Practices

### 1. Context Management
- Use CLAUDE.md for persistent project context
- Use skills for task-specific knowledge
- Use subagents for isolated tasks

### 2. Safety
- Configure hooks to block dangerous operations
- Use read-only subagents for analysis tasks
- Review generated code before execution

### 3. Efficiency
- Let Claude search and understand the codebase first
- Break complex tasks into subtasks
- Use checkpoints for long operations

### 4. Customization
- Create project-specific commands
- Define team conventions in CLAUDE.md
- Share useful subagents across projects

## Integration with Agent SDK

The Claude Agent SDK provides programmatic access to Claude Code's capabilities:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],
    cwd="/path/to/project"
)

async for message in query(prompt="Analyze this codebase", options=options):
    print(message)
```

See [Agent SDK documentation](./agent-sdk.md) for details.

## References

- [Claude Code Documentation](https://code.claude.com/docs)
- [GitHub Repository](https://github.com/anthropics/claude-code)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Hooks Configuration](https://claude.com/blog/how-to-configure-hooks)
