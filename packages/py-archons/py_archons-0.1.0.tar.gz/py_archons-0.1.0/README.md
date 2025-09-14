# py-archons

A simple Python package that provides a `get_names` function.

## Installation

```bash
pip install py-archons
```

## Usage

```python
from py_archons import get_names

names = get_names()
print(names)  # Output: ["guapo", "bandida"]
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