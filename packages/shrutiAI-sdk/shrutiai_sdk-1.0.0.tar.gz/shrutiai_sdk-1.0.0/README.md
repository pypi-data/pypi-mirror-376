# shrutiAI SDK

A Python SDK for interacting with shrutiAI API. This SDK provides a simple and intuitive interface for developers to integrate with your API service.

## Features

- 🔐 **API Key Authentication** - Secure authentication using API keys
- 🛡️ **Error Handling** - Comprehensive error handling with custom exceptions
- 📊 **Type Hints** - Full type hints for better IDE support
- 🔄 **Retry Logic** - Built-in retry mechanisms for network failures
- 📝 **Well Documented** - Extensive documentation and examples

## Installation

### From PyPI (when published)
```bash
pip install shrutiAI-sdk
```

### From Source
```bash
git clone https://github.com/yourusername/shrutiAI-sdk.git
cd shrutiAI-sdk
pip install -e .
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Quick Start

```python
from shrutiAI import ShrutiAIClient

# Initialize the client
client = ShrutiAIClient(api_key="your-api-key-here")

# Create a new user
user = client.create_user(
    name="John Doe",
    email="john.doe@example.com"
)

# Get all users
users = client.get_users(limit=10)

# Create a post
post = client.create_post(
    title="Hello World",
    content="This is my first post!",
    user_id=user['id']
)
```

## API Methods

### User Management
- `get_users(limit=10, offset=0)` - Get list of users
- `get_user(user_id)` - Get a specific user
- `create_user(name, email, **kwargs)` - Create a new user
- `update_user(user_id, **kwargs)` - Update a user
- `delete_user(user_id)` - Delete a user

### Posts Management
- `get_posts(user_id=None, limit=10)` - Get list of posts
- `create_post(title, content, user_id)` - Create a new post

### Analytics
- `get_analytics(start_date, end_date)` - Get analytics data

### Utility
- `health_check()` - Check API health
- `get_api_info()` - Get API information

## Error Handling

The SDK provides custom exceptions for different error scenarios:

```python
from shrutiAI import ShrutiAIClient, AuthenticationError, RateLimitError, NotFoundError

try:
    client = ShrutiAIClient("invalid-key")
    users = client.get_users()
except AuthenticationError:
    print("Invalid API key!")
except RateLimitError:
    print("Rate limit exceeded!")
except NotFoundError:
    print("Resource not found!")
```

## Configuration

You can customize the SDK behavior:

```python
# Custom base URL
client = ShrutiAIClient(
    api_key="your-key",
    base_url="https://your-custom-api.com/v1"
)
```

## Examples

See `example_usage.py` for a complete example of how to use the SDK.

```bash
python example_usage.py
```

## Development

### Setup Development Environment
```bash
pip install -e .[dev]
```

### Run Tests
```bash
pytest
```

### Code Formatting
```bash
black shrutiAI/
```

### Type Checking
```bash
mypy shrutiAI/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/shrutiAI-sdk/issues
- Email: your.email@example.com
