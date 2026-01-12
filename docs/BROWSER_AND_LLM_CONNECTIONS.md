# Browser and LLM Connection Reference

Quick reference for which files handle browser startup and LLM connections.

---

## Browser Startup Files

| File | Role | How |
|------|------|-----|
| **`browser_factory.py`** | **Single Source of Truth** | `BrowserFactory.create()` - tries 4 strategies |
| `explorer_agent.py` | Uses factory | `await BrowserFactory.create(headless=self.headless)` |
| `streaming_runner.py` | Uses factory | `await BrowserFactory.create(headless=headless)` |
| `base_service.py` | Uses factory | `await BrowserFactory.create(headless=self.headless)` |

### Browser Instantiation Chain

```
streaming_runner.py (or explorer_agent.py)
        |
        v
BrowserFactory.create()
        |
        v
Strategy 1: BrowserSession() + start()
Strategy 2: Browser()
Strategy 3: BrowserSession context manager
Strategy 4: Agent-managed
```

### Key Locations

- **Factory**: `backend/ui_testing_agent/core/browser_factory.py`
- **Strategies defined**: `BrowserFactory.STRATEGIES` list
- **Cleanup**: `BrowserFactory.cleanup(result)`
- **Agent kwargs**: `BrowserFactory.get_agent_kwargs(result)`

---

## LLM Connection Files

| File | Role | LLM Class |
|------|------|-----------|
| **`llm_factory.py`** | **Single Source of Truth** | `ChatGoogle`, `ChatOpenAI`, `ChatAnthropic` |
| `base_service.py` | Re-exports from llm_factory | (backward compatibility) |
| `explorer_agent.py` | Uses llm_factory | `get_llm()` |
| `streaming_runner.py` | Uses llm_factory | `get_llm()` |

### LLM Initialization Chain

```
Any service (explorer_agent.py, streaming_runner.py, base_service.py)
        |
        v
get_llm(model, temperature, api_key)  [from llm_factory.py]
        |
        v
ChatGoogle / ChatOpenAI / ChatAnthropic (based on model name)
```

### Key Locations

- **LLM Factory**: `backend/advanced_browser_services/llm_factory.py` - `get_llm()`
- **Deprecated alias**: `get_gemini_llm()` (calls `get_llm()` internally)
- **Default model**: `gemini-3-pro-preview`

### Model Detection Logic (llm_factory.py)

```python
def get_llm(model, temperature, api_key):
    if 'gemini' in model.lower() or 'gemma' in model.lower():
        return ChatGoogle(...)  # Uses GEMINI_API_KEY or GOOGLE_API_KEY
    elif 'gpt' in model.lower() or 'openai' in model.lower():
        return ChatOpenAI(...)  # Uses OPENAI_API_KEY
    elif 'claude' in model.lower() or 'anthropic' in model.lower():
        return ChatAnthropic(...)  # Uses ANTHROPIC_API_KEY
    else:
        return ChatGoogle(...)  # Default to Gemini
```

---

## Summary Table

| Concern | Primary File | Function |
|---------|--------------|----------|
| **Browser** | `browser_factory.py` | `BrowserFactory.create()` |
| **LLM** | `llm_factory.py` | `get_llm()` |

---

## Environment Variables

```bash
# For Gemini/Gemma models
GEMINI_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here

# For OpenAI/GPT models
OPENAI_API_KEY=your_key_here

# For Anthropic/Claude models
ANTHROPIC_API_KEY=your_key_here

# Optional: Force specific browser strategy
BROWSER_STRATEGY=browser_class  # or browser_session_with_start, context_manager, agent_managed
```
