# types-nameparser

[![PyPI version](https://badge.fury.io/py/types-nameparser.svg)](https://badge.fury.io/py/types-nameparser)
[![Python versions](https://img.shields.io/pypi/pyversions/types-nameparser.svg)](https://pypi.org/project/types-nameparser/)

Typing stubs for the [nameparser](https://github.com/derek73/python-nameparser) library.

## Overview

This package provides type information (stub files) for the `nameparser` library, enabling better IDE support and static type checking when working with human name parsing functionality.

The `nameparser` library is a Python library for parsing human names into their component parts (first name, last name, middle name, title, suffix, etc.), but it doesn't include type hints. This package fills that gap by providing comprehensive type stubs.

## Installation

```bash
pip install types-nameparser
```

Or if you're using [uv](https://github.com/astral-sh/uv):

```bash
uv add types-nameparser
```

## Usage

After installation, you can use the type stubs with your existing `nameparser` code:

```python
from nameparser import HumanName

# Now you get full type hints and IDE support!
name = HumanName("Dr. John Michael Smith Jr.")
print(name.first)    # "John"
print(name.last)     # "Smith" 
print(name.middle)   # "Michael"
print(name.title)    # "Dr."
print(name.suffix)   # "Jr."
```

## Type Information

The stubs provide type information for the `HumanName` class with the following properties:

- `first: str` - First name component
- `last: str` - Last name component  
- `middle: str` - Middle name component
- `title: str` - Title component (Mr., Mrs., Dr., etc.)
- `suffix: str` - Suffix component (Jr., Sr., III, etc.)
- `nickname: str` - Nickname component

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management and [just](https://github.com/casey/just) for task running.

### Setup

```bash
# Install dependencies
just install
```

### Available Commands

```bash
# Run linting
just lint

# Run linting with auto-fix
just lint-fix

# Format code
just format

# Type checking
just type-check

# Run tests
just test

# Run tests with coverage
just test-cov
```

## Requirements

- Python 3.10+
- The actual `nameparser` library (this package only provides type stubs)

## License

This project is licensed under the same terms as the original `nameparser` library.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Related Projects

- [nameparser](https://github.com/derek73/python-nameparser) - The original name parsing library
- [typeshed](https://github.com/python/typeshed) - Collection of type stubs for Python standard library and third-party packages
