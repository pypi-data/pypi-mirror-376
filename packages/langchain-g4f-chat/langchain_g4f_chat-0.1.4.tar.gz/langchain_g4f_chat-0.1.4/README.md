# LangChain G4F Integration

A LangChain integration for GPT4Free (g4f) that allows you to use any g4f provider with LangChain's chat model interface. This package eliminates the need for separate g4f installation.

## Features

- 🤖 **Full LangChain Compatibility**: Drop-in replacement for OpenAI chat models
- 🔄 **Multiple Providers**: Support for all g4f providers including your custom OpenRouterCustom
- 🌊 **Streaming Support**: Both sync and async streaming responses
- 🔐 **Authentication**: API key support for providers that require it
- ⚡ **Async Support**: Full async/await support for modern applications
- 🎛️ **Parameter Control**: Temperature, max_tokens, and other model parameters

## Installation

```bash
# Install the package (g4f is , no separate installation needed)
pip install langchain-g4f-chat

```

## Quick Start

```python
from langchain_g4f import ChatG4F

# Create a ChatG4F instance with correct model name
chat = ChatG4F(
    model="openai/gpt-3.5-turbo",  # ✅ Correct OpenRouter format
    provider=ChatG4F.Provider.OpenRouter,  #  Provider
    api_key="your-openrouter-api-key",
    temperature=0.7,
)

# Use with LangChain (when langchain-core is installed)
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is the capital of France?")
]

response = chat.invoke(messages)
print(response.content)
```

## Basic Usage (Without LangChain Core)

```python
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f  # Import the  g4f

# Create ChatG4F instance
chat = ChatG4F(
    model="gpt-3.5-turbo",
    provider=lg4f.Provider.OpenRouterCustom,  # Use  Provider
    api_key="your-api-key",
    temperature=0.7,
)

# Use g4f directly with ChatG4F parameters
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
]

response = lg4f.ChatCompletion.create(  # Use  ChatCompletion
    model=chat.model_name,
    messages=messages,
    provider=chat.provider,
    api_key=chat.api_key.get_secret_value() if chat.api_key else None,
    temperature=chat.temperature,
)

print(response)
```

## Advanced Usage

### Multiple Providers

```python
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f

# Try different providers with fallback
providers = [
    lg4f.Provider.OpenRouterCustom,  # Use  Provider
    lg4f.Provider.OpenAI,
    None,  # Auto-select
]

for provider in providers:
    try:
        chat = ChatG4F(
            model="gpt-3.5-turbo",
            provider=provider,
            api_key="your-key" if provider else None
        )
        # Use the chat model
        break
    except Exception as e:
        print(f"Provider {provider} failed: {e}")
        continue
```

### Streaming Responses

```python
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f

# Enable streaming
chat = ChatG4F(
    model="gpt-3.5-turbo",
    provider=lg4f.Provider.OpenRouterCustom,  # Use  Provider
    api_key="your-key",
    stream=True
)

# Stream with g4f directly
response = lg4f.ChatCompletion.create(  # Use  ChatCompletion
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a story"}],
    provider=lg4f.Provider.OpenRouterCustom,
    api_key="your-key",
    stream=True
)

for chunk in response:
    print(chunk, end='', flush=True)
```

### Image Input (Vision Models)

```python
from langchain_core.messages import HumanMessage

# Using image URL
chat = ChatG4F(
    model="openai/gpt-4-vision-preview",  # Vision model
    provider=g4f.Provider.OpenRouterCustom,
    api_key="your-key"
)

# Option 1: Direct multimodal content
message = HumanMessage(content=[
    {"type": "text", "text": "What's in this image?"},
    {
        "type": "image_url",
        "image_url": {"url": "https://example.com/image.jpg"}
    }
])

response = chat.invoke([message])
print(response.content)

# Option 2: Base64 encoded image
import base64
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

message = HumanMessage(content=[
    {"type": "text", "text": "Describe this image"},
    {
        "type": "image_url", 
        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
    }
])

response = chat.invoke([message])
print(response.content)

# Option 3: Anthropic-style format (automatically converted)
message = HumanMessage(content=[
    {"type": "text", "text": "What do you see?"},
    {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": image_data
        }
    }
])

response = chat.invoke([message])
print(response.content)
```

### Multiple Provider Examples

```python
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f

# DeepInfra Provider
chat_deepinfra = ChatG4F(
    model="meta-llama/Llama-2-70b-chat-hf",
    provider=lg4f.Provider.DeepInfra,  # Use  Provider
    # No API key needed for many models
)

# HuggingChat Provider  
chat_hugging = ChatG4F(
    model="microsoft/DialoGPT-medium",
    provider=lg4f.Provider.HuggingChat,  # Use  Provider
)

# Blackbox Provider
chat_blackbox = ChatG4F(
    model="gpt-3.5-turbo",
    provider=lg4f.Provider.Blackbox,  # Use  Provider
)

# Try multiple providers with fallback
providers_to_try = [
    (lg4f.Provider.OpenRouterCustom, "openai/gpt-3.5-turbo", "your-key"),  # Use  Provider
    (lg4f.Provider.DeepInfra, "meta-llama/Llama-2-7b-chat-hf", None),
    (lg4f.Provider.HuggingChat, "microsoft/DialoGPT-medium", None),
    (lg4f.Provider.Blackbox, "gpt-3.5-turbo", None),
]

for provider, model, api_key in providers_to_try:
    try:
        chat = ChatG4F(
            model=model,
            provider=provider,
            api_key=api_key if api_key else None
        )
        response = chat.invoke([HumanMessage(content="Hello!")])
        print(f"Success with {provider.__name__}: {response.content}")
        break
    except Exception as e:
        print(f"Provider {provider.__name__} failed: {e}")
        continue
```

### Async Usage

```python
import asyncio
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f

async def chat_async():
    chat = ChatG4F(
        model="gpt-3.5-turbo",
        provider=lg4f.Provider.OpenRouterCustom,  # Use  Provider
        api_key="your-key"
    )
    
    # Use with LangChain async methods (when available)
    # response = await chat.ainvoke(messages)
    
    # Or use g4f async directly
    response = await lg4f.ChatCompletion.create_async(  # Use  ChatCompletion
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}],
        provider=lg4f.Provider.OpenRouterCustom,
        api_key="your-key"
    )
    
    return response

# Run async
result = asyncio.run(chat_async())
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | "gpt-3.5-turbo" | Model name to use |
| `provider` | Any | None | G4F provider (auto-select if None) |
| `api_key` | str | None | API key for authenticated providers |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_tokens` | int | None | Maximum tokens to generate |
| `stream` | bool | False | Enable streaming responses |
| `model_kwargs` | dict | {} | Additional parameters for g4f |

## Supported Providers

- **OpenRouterCustom**: Your custom OpenRouter provider ✅
- **OpenAI**: Official OpenAI API
- **Bing**: Microsoft Bing Chat
- **Claude**: Anthropic Claude models
- **Auto**: Let g4f choose the best available provider


## Integration with LangChain

Once you have `langchain-core` installed, you can use ChatG4F with:

- **LangChain Chains**: Use in sequential chains
- **LangChain Agents**: As the LLM for AI agents
- **Memory**: With conversation memory
- **Callbacks**: Full callback support
- **Async**: Async chains and operations

```python
# Example with LangChain chain (requires langchain-core)
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["question"],
    template="Answer this question: {question}"
)

chain = LLMChain(llm=chat, prompt=prompt)
result = chain.run("What is AI?")
```

## Error Handling

```python
from langchain_g4f import ChatG4F
import langchain_g4f as lg4f

try:
    chat = ChatG4F(
        model="gpt-4",
        provider=lg4f.Provider.OpenRouterCustom,  # Use  Provider
        api_key="your-key"
    )
    
    response = lg4f.ChatCompletion.create(  # Use  ChatCompletion
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}],
        provider=lg4f.Provider.OpenRouterCustom,
        api_key="your-key"
    )
    
except Exception as e:
    print(f"Error: {e}")
    # Fallback to different provider or model
```

## Troubleshooting

### Import Error: No module named 'langchain_g4f'

If you get this error even after installing the package:

1. **Check installation**:
   ```bash
   pip list | grep langchain-g4f-chat
   ```

2. **Reinstall the package**:
   ```bash
   pip uninstall langchain-g4f-chat -y
   pip install langchain-g4f-chat
   ```

3. **For development mode**:
   ```bash
   cd langchain_g4f
   pip install -e .
   ```

4. **Verify import**:
   ```python
   from langchain_g4f import ChatG4F
   print("Import successful!")
   ```

### Common Issues

- **Model not found**: Use providers that support your model or let g4f auto-select
- **API key errors**: Ensure you're using the correct API key for authenticated providers
- **Rate limits**: Some providers have rate limits; try different providers if one fails

## Module Structure

```
langchain_g4f/
├── __init__.py           # Main exports
├── requirements.txt      # Dependencies (includes g4f requirements)
├── setup.py             # Package setup
├── g4f/                 # g4f
│   ├── __init__.py
│   ├── base/
│   ├── providers/
│   └── ...
├── core/                # Core utilities
├── text/                # Text/chat models
└── images/              # Image generation
```

## Development

To install in development mode (g4f is , no separate installation needed):

```bash
cd langchain_g4f
pip install -e .
```

## Testing

Run the test scripts to verify functionality:

```bash
python test_langchain_g4f_practical.py
python test_complete_integration.py
```

## License

MIT License - Feel free to use and modify as needed.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

