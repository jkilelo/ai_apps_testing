# Function Calling & Tools

Gemini models can interact with external systems through function calling and built-in tools. This enables agentic capabilities where the model can take actions and retrieve real-time information.

## Overview

The SDK supports two types of tools:
1. **Custom Functions** - Your own Python functions the model can call
2. **Built-in Tools** - Google-provided tools (Search, Code Execution, etc.)

## Automatic Function Calling (AFC)

The simplest approach - pass Python functions directly and the SDK handles everything.

### Basic Example

```python
from google import genai
from google.genai import types

client = genai.Client(api_key='YOUR_API_KEY')

def get_weather(location: str) -> str:
    """Get the current weather for a location.

    Args:
        location: City and state, e.g., "San Francisco, CA"

    Returns:
        Weather description
    """
    # Your actual implementation here
    return f"The weather in {location} is sunny and 72°F"

def get_stock_price(symbol: str) -> str:
    """Get the current stock price.

    Args:
        symbol: Stock ticker symbol, e.g., "GOOGL"

    Returns:
        Current stock price
    """
    # Your actual implementation here
    return f"{symbol} is trading at $150.25"

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='What is the weather in Boston and the stock price of GOOGL?',
    config=types.GenerateContentConfig(
        tools=[get_weather, get_stock_price]
    )
)

print(response.text)
# Output: The weather in Boston is sunny and 72°F. GOOGL is trading at $150.25.
```

### How AFC Works

1. Model receives prompt and available functions
2. Model decides which function(s) to call with what arguments
3. SDK automatically executes the functions
4. Results are sent back to the model
5. Model generates final response

## Manual Function Calling

For more control over function execution:

### Define Function Declaration

```python
from google.genai import types

# Define function schema
weather_function = types.FunctionDeclaration(
    name='get_weather',
    description='Get the current weather for a location',
    parameters_json_schema={
        'type': 'object',
        'properties': {
            'location': {
                'type': 'string',
                'description': 'City and state, e.g., San Francisco, CA'
            },
            'unit': {
                'type': 'string',
                'enum': ['celsius', 'fahrenheit'],
                'description': 'Temperature unit'
            }
        },
        'required': ['location']
    }
)

tool = types.Tool(function_declarations=[weather_function])
```

### Handle Function Calls

```python
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='What is the weather in Tokyo?',
    config=types.GenerateContentConfig(tools=[tool])
)

# Check for function call
if response.candidates[0].content.parts[0].function_call:
    fc = response.candidates[0].content.parts[0].function_call
    print(f"Function: {fc.name}")
    print(f"Arguments: {fc.args}")

    # Execute your function
    result = your_weather_function(**fc.args)

    # Send result back to model
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=[
            types.Content(role='user', parts=[
                types.Part.from_text('What is the weather in Tokyo?')
            ]),
            types.Content(role='model', parts=[
                types.Part.from_function_call(fc)
            ]),
            types.Content(role='function', parts=[
                types.Part.from_function_response(
                    name=fc.name,
                    response={'result': result}
                )
            ])
        ],
        config=types.GenerateContentConfig(tools=[tool])
    )

    print(response.text)
```

### Disable Automatic Calling

```python
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='What is the weather?',
    config=types.GenerateContentConfig(
        tools=[get_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        )
    )
)

# Now handle function calls manually
```

## Built-in Tools

### Google Search

Ground responses in real-time web search results:

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='What are the latest developments in AI?',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ]
    )
)

print(response.text)

# Access grounding metadata
if response.candidates[0].grounding_metadata:
    for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
        print(f"Source: {chunk.web.uri}")
```

### Code Execution

Let the model write and run Python code:

```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Calculate the factorial of 10 and find all prime numbers up to 50',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(code_execution=types.ToolCodeExecution())
        ]
    )
)

print(response.text)

# Access executed code and results
for part in response.candidates[0].content.parts:
    if part.executable_code:
        print("Code executed:")
        print(part.executable_code.code)
    if part.code_execution_result:
        print("Result:")
        print(part.code_execution_result.output)
```

**Available Libraries in Code Execution:**
- NumPy
- SymPy

**Note:** You cannot install custom libraries in code execution.

### URL Context

Extract and use content from URLs:

```python
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Summarize the main points from https://example.com/article',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(url_context=types.UrlContext())
        ]
    )
)
```

### File Search

Search uploaded files:

```python
# First upload files
file1 = client.files.upload(file='document1.pdf')
file2 = client.files.upload(file='document2.pdf')

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Find information about pricing in the uploaded documents',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(file_search=types.FileSearch(
                file_ids=[file1.name, file2.name]
            ))
        ]
    )
)
```

## Function Calling with Chat

```python
def search_products(query: str, max_results: int = 5) -> str:
    """Search for products in the catalog."""
    return f"Found {max_results} results for '{query}'"

def add_to_cart(product_id: str, quantity: int = 1) -> str:
    """Add a product to the shopping cart."""
    return f"Added {quantity} of product {product_id} to cart"

chat = client.chats.create(
    model='gemini-3-flash-preview',
    config=types.GenerateContentConfig(
        tools=[search_products, add_to_cart],
        system_instruction='You are a shopping assistant.'
    )
)

response = chat.send_message('Find me some running shoes')
print(response.text)

response = chat.send_message('Add the first one to my cart')
print(response.text)
```

## Combining Multiple Tools

```python
def get_user_info(user_id: str) -> dict:
    """Get user profile information."""
    return {'name': 'John', 'email': 'john@example.com'}

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Get info for user 123 and search the web for their company',
    config=types.GenerateContentConfig(
        tools=[
            get_user_info,
            types.Tool(google_search=types.GoogleSearch())
        ]
    )
)
```

**Note:** Gemini 3 does not support combining built-in tools with custom function calling in the same request.

## Parallel Function Calling

The model can call multiple functions simultaneously:

```python
def get_temperature(city: str) -> str:
    return f"{city}: 72°F"

def get_humidity(city: str) -> str:
    return f"{city}: 65%"

def get_wind_speed(city: str) -> str:
    return f"{city}: 10 mph"

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents='Get all weather metrics for New York',
    config=types.GenerateContentConfig(
        tools=[get_temperature, get_humidity, get_wind_speed]
    )
)
```

## Best Practices

### 1. Write Clear Docstrings

The model uses docstrings to understand function purpose:

```python
def calculate_mortgage(
    principal: float,
    annual_rate: float,
    years: int
) -> dict:
    """Calculate monthly mortgage payment and total cost.

    Args:
        principal: Loan amount in dollars
        annual_rate: Annual interest rate as decimal (e.g., 0.05 for 5%)
        years: Loan term in years

    Returns:
        Dictionary with monthly_payment and total_cost
    """
    # Implementation
```

### 2. Use Type Hints

Type hints help generate accurate function schemas:

```python
from typing import List, Optional

def search_items(
    query: str,
    category: Optional[str] = None,
    max_results: int = 10,
    include_details: bool = False
) -> List[dict]:
    """Search for items."""
    pass
```

### 3. Handle Errors Gracefully

```python
def risky_operation(param: str) -> str:
    """Perform an operation that might fail."""
    try:
        result = do_something(param)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### 4. Validate Inputs

```python
def transfer_money(amount: float, recipient: str) -> str:
    """Transfer money to a recipient."""
    if amount <= 0:
        return "Error: Amount must be positive"
    if not recipient:
        return "Error: Recipient required"
    # Proceed with transfer
    return f"Transferred ${amount} to {recipient}"
```

## Thought Signatures in Function Calling

**Important:** For Gemini 3, thought signatures are **required** for function calling. Missing signatures result in a 400 error.

The SDK handles this automatically when using `client.chats` or maintaining proper conversation history. For manual implementations, ensure you preserve and return thought signatures in multi-turn function calling flows.

## When to Use Each Approach

| Scenario | Recommendation |
|----------|----------------|
| Quick prototyping | Automatic Function Calling |
| Production with custom logic | Manual Function Calling |
| Real-time information | Google Search |
| Mathematical computations | Code Execution |
| Document Q&A | File Search |
| Complex multi-step workflows | Manual with conversation history |

## References

- [Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling)
- [Code Execution](https://ai.google.dev/gemini-api/docs/code-execution)
- [Grounding with Search](https://ai.google.dev/gemini-api/docs/grounding)
