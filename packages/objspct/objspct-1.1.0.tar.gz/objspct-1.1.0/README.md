# ObjSpct

objspct is a Python introspection tool that lets you explore any Python object. Whether you’re debugging, learning a library, or documenting your code, objspct gives you a rich, structured overview of an object’s attributes, methods, properties, and more — all in a beautifully formatted tree using Rich.

## Features

Deep object introspection: Inspect types, classes, methods, properties, and attributes.
Classify members intelligently: Automatically separates magic methods, internal/external methods, and attributes.
Property-aware: Detects and lists properties separately.
Pretty-print with Rich: Generates a tree view that’s easy to read and understand.
Flexible filtering: Skip empty fields or select which categories to display.

## Installation

```bash
pip install objspct
```

## Usage

```python
from objspct import inspect_object

class MyClass:
    def __init__(self):
        self.public_attr = 42
        self._internal_attr = "secret"

    @property
    def computed(self):
        return self.public_attr * 2

    def public_method(self):
        return "Hello"

    def _internal_method(self):
        return "Internal"

obj = MyClass()
inspect_object(obj)
```

This will output a rich, hierarchical tree showing all categorized members of the object.
___

### Filtering

```python
# Only display methods and properties
inspect_object(obj, categories=["methods_external", "properties"])
```
___

### Skip Empty Attributes
```python
# Skip empty attributes in the tree
inspect_object(obj, skip_empty=True)
```
___

## Why Use objspct?

- Learn unfamiliar objects and libraries quickly.
- Debug complex classes or instances without manually exploring dir() or inspect.
- Document object structures visually.
- Perfect for teaching or self-learning Python OOP patterns.