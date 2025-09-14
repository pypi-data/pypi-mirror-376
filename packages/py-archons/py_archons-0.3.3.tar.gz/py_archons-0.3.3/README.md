# py-archons

A simple Python package that provides `get_names`, `get_cities`, and `get_countries` functions.

## Installation

```bash
pip install py-archons
```

## Usage

```python
from py_archons import get_names, get_cities, get_countries

names = get_names()
print(names)  # Output: ["guapo", "bandida"]

cities = get_cities()
print(cities)  # Output: ["new york", "london"]

countries = get_countries()
print(countries)  # Output: ["united states", "united kingdom"]
```

## Development

To install in development mode:

```bash
pip install -e .
```

## Building and Publishing

### Automated Publishing (Recommended)

Use the `publish.py` script for a complete workflow. The script automatically:
- Reads the current version from `version.py`
- Checks if the version already exists on PyPI
- Prevents duplicate uploads
- Updates version only when specified

```bash
# Publish current version from version.py (smart - checks if version exists)
python publish.py

# Test current version with TestPyPI
python publish.py --test

# Just build current version without uploading
python publish.py --build-only

# Update to specific version and publish
python publish.py 0.4.0

# Using shell script (auto-activates venv)
./publish.sh
./publish.sh --test
```

### Manual Publishing

```bash
# Edit version in py_archons/version.py, then:
python -m build
python -m twine upload dist/py_archons-*
```

## Version Management

### Yanking (Deprecating) Versions

```bash
# Yank a version from PyPI (marks as deprecated but keeps available)
python yank_version.py 0.3.0

# Yank from TestPyPI
python yank_version.py 0.3.0 --test
```

### Adding Deprecation Notices

```bash
# Get guidance on adding deprecation notices
python deprecate_version.py 0.3.0 "Security issues"
```

## License

MIT License