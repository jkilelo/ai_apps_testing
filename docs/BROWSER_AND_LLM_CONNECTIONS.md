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
    model_lower = model.lower()

    if 'gemini' in model_lower or 'gemma' in model_lower:
        # Uses GOOGLE_API_KEY (checked first) or GEMINI_API_KEY
        return ChatGoogle(model, temperature, api_key)

    elif 'gpt' in model_lower or 'openai' in model_lower:
        # Uses OPENAI_API_KEY (via ChatOpenAI)
        return ChatOpenAI(model, temperature)

    elif 'claude' in model_lower or 'anthropic' in model_lower:
        # Uses ANTHROPIC_API_KEY (via ChatAnthropic)
        return ChatAnthropic(model, temperature)

    else:
        # Default to Gemini
        return ChatGoogle(model, temperature, api_key)
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
# For Gemini/Gemma models (GOOGLE_API_KEY checked first)
GOOGLE_API_KEY=your_key_here
# or (fallback)
GEMINI_API_KEY=your_key_here

# For OpenAI/GPT models
OPENAI_API_KEY=your_key_here

# For Anthropic/Claude models
ANTHROPIC_API_KEY=your_key_here

# Optional: Force specific browser strategy
BROWSER_STRATEGY=browser_session_with_start  # default
# Other options: browser_class, context_manager, agent_managed
```
