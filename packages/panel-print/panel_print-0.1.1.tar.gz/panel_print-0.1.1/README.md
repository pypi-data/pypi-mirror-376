# Panel Print

A Python library that provides beautiful console output using Rich panels for enhanced debugging and data visualization.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.1-brightgreen.svg)](https://github.com/yourusername/panel-print)

## Features

- 🎨 **Beautiful Output**: Pretty print objects in elegant Rich panels
- 📦 **Easy to Use**: Simple API with just one main function
- 🔧 **Customizable**: Configurable max length for container abbreviation
- 🚀 **Fast**: Built on top of the powerful Rich library
- 🐍 **Modern Python**: Supports Python 3.10+

## Installation

Install using pip:

```bash
pip install panel-print
```

Or using uv:

```bash
uv add panel-print
```

## Quick Start

```python
from panel_print import pp

# Pretty print any Python object
data = {
    "name": "John Doe", 
    "age": 30,
    "skills": ["Python", "JavaScript", "Go"],
    "address": {
        "street": "123 Main St",
        "city": "San Francisco",
        "state": "CA"
    }
}

pp(data)
```

## Usage Examples

### Basic Usage

```python
from panel_print import pp

# Print simple values
pp("Hello, World!")
pp(42)
pp([1, 2, 3, 4, 5])
```

### Multiple Objects

```python
from panel_print import pp

# Print multiple objects at once
pp("User Info:", {"name": "Alice", "age": 25}, ["admin", "user"])
```

### Custom Max Length

```python
from panel_print import pp

# Control container abbreviation
long_list = list(range(100))
pp(long_list, max_length=10)  # Will abbreviate after 10 items
```

### Complex Data Structures

```python
from panel_print import pp

# Works great with nested data
config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "credentials": {
            "username": "admin",
            "password": "secret"
        }
    },
    "features": ["auth", "logging", "caching"],
    "debug": True
}

pp(config)
```

### Integration with Rich

```python
from panel_print import print, pprint

# Access Rich's print and pprint directly
print("This uses Rich's enhanced print")
pprint({"key": "value"})  # Rich's pretty print without panels
```

## API Reference

### `pp(*objects, max_length=20)`

Pretty print objects in a panel format.

**Parameters:**

- `*objects` (Any): One or more objects to pretty print
- `max_length` (int, optional): Maximum length of containers before abbreviating. Defaults to 20.

**Returns:**

- None

**Example:**

```python
pp(data, max_length=50)
```

## Advanced Usage

### Debugging Complex Objects

```python
from panel_print import pp
import datetime

class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.created_at = datetime.datetime.now()
    
    def __repr__(self):
        return f"User(name='{self.name}', email='{self.email}')"

user = User("Alice", "alice@example.com")
pp("Debug User Object:", user, user.__dict__)
```

### Working with APIs

```python
import requests
from panel_print import pp

response = requests.get("https://api.github.com/users/octocat")
pp("GitHub API Response:", response.json())
```

## Requirements

- Python 3.10 or higher
- Rich >= 14.1.0

## Development

### Setting up Development Environment

1. Clone the repository:

```bash
git clone https://github.com/yourusername/panel-print.git
cd panel-print
```

2. Install dependencies using uv:

```bash
uv sync
```

3. Run tests:

```bash
uv run pytest
```

### Building the Package

```bash
uv build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) - Python library for rich text and beautiful formatting
- Inspired by the need for better debugging output in Python applications

## Changelog

### v0.1.1

- Initial release
- Basic panel printing functionality
- Support for multiple objects
- Configurable max length parameter

---

Made with ❤️ for the Python community
