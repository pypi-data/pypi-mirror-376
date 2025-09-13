# APICrusher Lite

Open source AI model router that automatically reduces API costs by routing simple queries to cheaper models.

## The Problem

You're using GPT-5 or Claude Opus 4.1 for everything. Even for tasks like:
- Formatting JSON
- Extracting emails from text
- Basic string operations
- Simple yes/no questions

That's like hiring a brain surgeon to apply band-aids.

## The Solution

This lightweight router analyzes query complexity and automatically routes simple requests to cheaper models while preserving quality for complex tasks.

```python
# Before: Everything goes to expensive models
response = openai.chat.completions.create(
    model="gpt-5",  # $1.25/$10 per million tokens (input/output)
    messages=[{"role": "user", "content": "Extract the email from: Contact john@example.com"}]
)

# After: Simple tasks use cheaper models automatically
from apicrusher_lite import Router

router = Router()
model = router.route("gpt-5", messages)  # Returns "gpt-5-nano" for simple tasks
response = openai.chat.completions.create(model=model, messages=messages)
```

## Installation

```bash
pip install apicrusher-lite
```

## Basic Usage

```python
from apicrusher_lite import Router

# Initialize router
router = Router()

# Your messages
messages = [
    {"role": "user", "content": "What's the capital of France?"}
]

# Get optimal model for this query
optimal_model = router.route("gpt-5", messages)
print(f"Using {optimal_model} instead of gpt-5")  # "Using gpt-5-nano instead of gpt-5"

# Use with your existing OpenAI code
import openai
response = openai.chat.completions.create(
    model=optimal_model,
    messages=messages
)
```

## How It Works

The router analyzes your messages for complexity indicators:
- Length and structure
- Code blocks
- Data processing requirements
- Reasoning complexity
- Output format requirements

Simple queries (complexity < 0.3) get routed to cheaper models.

## Supported Model Mappings (September 2025)

| Original Model | Simple Task Routes To | Original Cost | Optimized Cost | Savings |
|---------------|----------------------|---------------|----------------|---------|
| gpt-5 | gpt-5-nano | $1.25/$10 | $0.05/$0.40 | 96% |
| gpt-5-turbo | gpt-5-nano | $0.60/$2.40 | $0.05/$0.40 | 92% |
| claude-opus-4.1 | claude-3-haiku | $15/$75 | $0.25/$1.25 | 98% |
| claude-sonnet-4 | claude-3-haiku | $3/$15 | $0.25/$1.25 | 92% |
| gemini-2.5-pro | gemini-2.5-flash-lite | $1.25/$5 | $0.10/$0.40 | 92% |
| grok-4 | grok-3-mini | $3/$15 | $1/$3 | 67% |

*Costs shown as input/output per million tokens*

## Examples

```python
# Example 1: Simple extraction (routes to nano/mini model)
messages = [{"role": "user", "content": "Extract the date: Meeting on Jan 15, 2025"}]
model = router.route("gpt-5", messages)  # Returns "gpt-5-nano"

# Example 2: Complex reasoning (keeps original model)  
messages = [{"role": "user", "content": "Analyze this code for security vulnerabilities and suggest improvements: [500 lines of code]"}]
model = router.route("gpt-5", messages)  # Returns "gpt-5"

# Example 3: Check complexity score
complexity = router.analyze_complexity(messages)
print(f"Complexity: {complexity}")  # 0.1 for simple, 0.9 for complex
```

## Testing

Run the test suite to verify functionality:

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Or run specific test
python tests/test_router.py
```

The test suite includes:
- Simple query routing validation
- Complex query preservation tests  
- Complexity analysis verification
- Model mapping accuracy checks

## Development

```bash
# Clone the repository
git clone https://github.com/apicrusher/apicrusher-lite.git
cd apicrusher-lite

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Limitations

This is the basic open-source router. It does NOT include:
- ❌ Real-time model pricing updates
- ❌ Response caching
- ❌ Cross-provider routing (GPT→Claude)
- ❌ Usage analytics
- ❌ Context compression
- ❌ Automatic fallback for deprecated models

## Want 73-99% Cost Savings?

This lite version provides basic routing within the same provider. 

For enterprise features including:
- ✅ Real-time optimization rules updated daily
- ✅ Intelligent caching (30% hit rate)
- ✅ Cross-provider routing (route GPT-5 queries to Claude Haiku)
- ✅ Analytics dashboard with ROI tracking
- ✅ Context compression (77% token reduction)
- ✅ Model deprecation handling

Check out **[APICrusher Pro](https://apicrusher.com)** - from $99/month with a 7-day free trial.

## Basic Router Implementation

```python
class Router:
    def __init__(self):
        self.model_map = {
            "gpt-5": "gpt-5-nano",
            "gpt-5-turbo": "gpt-5-nano", 
            "gpt-4": "gpt-4o-mini",
            "claude-opus-4.1-20250805": "claude-3-haiku-20240307",
            "claude-sonnet-4-20250222": "claude-3-haiku-20240307",
            # ... more mappings
        }
    
    def analyze_complexity(self, messages):
        # Basic complexity analysis
        text = str(messages)
        complexity = 0.1
        
        if len(text) > 500: complexity += 0.3
        if "```" in text: complexity += 0.3  # Has code
        if any(word in text.lower() for word in ['analyze', 'explain', 'complex']):
            complexity += 0.3
            
        return min(complexity, 1.0)
    
    def route(self, model, messages):
        complexity = self.analyze_complexity(messages)
        
        if complexity < 0.3 and model in self.model_map:
            return self.model_map[model]
        
        return model
```

## Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure tests pass (`python -m pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - See [LICENSE](LICENSE) for details.

## Support

- GitHub Issues: [github.com/apicrusher/apicrusher-lite/issues](https://github.com/apicrusher/apicrusher-lite/issues)
- Email: hello@apicrusher.com

## Disclaimer

This tool is provided as-is. Always test with your specific use cases. Some complex queries incorrectly routed to simple models may produce lower quality results.

---

*Built by developers who were spending $8k/month on uppercase conversions. We learned our lesson.*
