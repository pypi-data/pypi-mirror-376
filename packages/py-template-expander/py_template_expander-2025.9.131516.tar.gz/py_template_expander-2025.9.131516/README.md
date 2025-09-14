[![PyPI version](https://badge.fury.io/py/py_template_expander.svg)](https://badge.fury.io/py/py_template_expander)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/py_template_expander)](https://pepy.tech/project/py_template_expander)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# py_template_expander

A Python package that expands template strings with various placeholders including optional groups, alternatives, and character sets.

## Installation

To install `py_template_expander`, use pip:

```bash
pip install py_template_expander
```

## Usage

The `expand` function takes a template string and yields all possible expanded strings.

Here's a simple example:

```python
from py_template_expander import expand

template1 = "Hello (world|there)!"
print("Expanding: ", template1)
for expansion in expand(template1):
    print(expansion)
# Expected output:
# Expanding:  Hello (world|there)!
# Hello world!
# Hello there!

template2 = "The quick [abc] fox."
print("\nExpanding: ", template2)
for expansion in expand(template2):
    print(expansion)
# Expected output:
# Expanding:  The quick [abc] fox.
# The quick a fox.
# The quick b fox.
# The quick c fox.

template3 = "Optional: (item1|item2) and (optional|)"
print("\nExpanding: ", template3)
for expansion in expand(template3):
    print(expansion)
# Expected output:
# Expanding:  Optional: (item1|item2) and (optional|)
# Optional: item1 and optional
# Optional: item1 and
# Optional: item2 and optional
# Optional: item2 and
# Optional:  and optional
# Optional:  and
```

## Features

- **Optional Groups**: Use `(pattern)` for parts that may or may not appear.
- **Alternatives**: Use `|` within parentheses to specify choices, e.g., `(A|B)`.
- **Character Sets**: Use `[abc]` to match any single character within the brackets.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/py_template_expander/issues).

## License

`py_template_expander` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Author

**Eugene Evstafev**
- LinkedIn: [eugene-evstafev-716669181](https://www.linkedin.com/in/eugene-evstafev-716669181/)
- Email: hi@eugene.plus

## Repository

[https://github.com/chigwell/py_template_expander](https://github.com/chigwell/py_template_expander)