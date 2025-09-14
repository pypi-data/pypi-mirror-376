# py-archons

A simple Python package that provides `get_names` and `get_cities` functions.

## Installation

```bash
pip install py-archons
```

## Usage

```python
from py_archons import get_names, get_cities

names = get_names()
print(names)  # Output: ["guapo", "bandida"]

cities = get_cities()
print(cities)  # Output: ["new york", "london"]
```

## Development

To install in development mode:

```bash
pip install -e .
```

## Building for PyPI

```bash
pip install build twine
python -m build
python -m twine upload dist/*
```

## License

MIT License