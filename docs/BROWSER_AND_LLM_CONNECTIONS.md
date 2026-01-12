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
| **`base_service.py`** | `get_gemini_llm()` | `ChatGoogle` |
| **`explorer_agent.py`** | `get_llm()` | `ChatGoogle`, `ChatOpenAI`, `ChatAnthropic` |
| `streaming_runner.py` | Uses `get_gemini_llm()` | (imports from base_service) |

### LLM Initialization Chain

```
streaming_runner.py
        |
        v
get_gemini_llm(model, temperature)  [from base_service.py]
        |
        v
ChatGoogle(model=..., temperature=...)
```

```
explorer_agent.py
        |
        v
get_llm(model, temperature, api_key)  [local function]
        |
        v
ChatGoogle / ChatOpenAI / ChatAnthropic (based on model name)
```

### Key Locations

- **Gemini-only LLM**: `backend/advanced_browser_services/base_service.py:31` - `get_gemini_llm()`
- **Multi-provider LLM**: `backend/ui_testing_agent/core/explorer_agent.py:37` - `get_llm()`
- **Default model**: `gemini-3-pro-preview`

### Model Detection Logic (explorer_agent.py)

```python
def get_llm(model, temperature, api_key):
    if 'gemini' in model.lower() or 'gemma' in model.lower():
        return ChatGoogle(...)
    elif 'gpt' in model.lower():
        return ChatOpenAI(...)
    elif 'claude' in model.lower():
        return ChatAnthropic(...)
    else:
        return ChatGoogle(...)  # Default
```

---

## Summary Table

| Concern | Primary File | Function |
|---------|--------------|----------|
| **Browser** | `browser_factory.py` | `BrowserFactory.create()` |
| **LLM (Gemini only)** | `base_service.py` | `get_gemini_llm()` |
| **LLM (Multi-provider)** | `explorer_agent.py` | `get_llm()` |

---

## Environment Variables

```bash
# Required for LLM
GEMINI_API_KEY=your_key_here
# or
GOOGLE_API_KEY=your_key_here

# Optional: Force specific browser strategy
BROWSER_STRATEGY=browser_class  # or browser_session_with_start, context_manager, agent_managed
```
