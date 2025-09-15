[![PyPI version](https://badge.fury.io/py/exrex_variant_generator.svg)](https://badge.fury.io/py/exrex_variant_generator)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/exrex_variant_generator)](https://pepy.tech/project/exrex_variant_generator)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# exrex_variant_generator

`exrex_variant_generator` is a Python package that leverages regular expressions to generate all possible string variants. It can handle standard regex patterns by expanding them into all matching strings, or it can interpret custom string formats with bracketed options to generate combinations.

## Installation

To install `exrex_variant_generator`, use pip:

```bash
pip install exrex_variant_generator
```

## Usage

Using `exrex_variant_generator` is straightforward.

### Generating variants from a custom string with options:

This mode interprets strings like `'a[bc]d'` to generate combinations.

```python
from exrex_variant_generator import generate_variants

custom_pattern = 'user[123]_pref[a|b]'
variants = generate_variants(custom_pattern)
print(variants)
# Output: ['user1_prefa', 'user1_pref b', 'user2_prefa', 'user2_pref b', 'user3_prefa', 'user3_pref b']
```

### Generating variants from a strict regex pattern:

This mode uses the `exrex` library to generate all strings matching a given regex.

```python
from exrex_variant_generator import generate_variants

regex_pattern = '[a-c]{2}'
variants = generate_variants(regex_pattern)
print(variants)
# Output: ['aa', 'ab', 'ac', 'ba', 'bb', 'bc', 'ca', 'cb', 'cc']
```

## Author

*   Eugene Evstafev <hi@eugene.plus> - [LinkedIn](https://www.linkedin.com/in/eugene-evstafev-716669181/)

## Repository

*   [GitHub](https://github.com/chigwell/exrex_variant_generator)

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/exrex_variant_generator/issues).

## License

`exrex_variant_generator` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).