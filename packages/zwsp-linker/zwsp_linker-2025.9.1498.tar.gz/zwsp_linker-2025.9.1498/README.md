[![PyPI version](https://badge.fury.io/py/zwsp_linker.svg)](https://badge.fury.io/py/zwsp_linker)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/zwsp_linker)](https://pepy.tech/project/zwsp_linker)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# zwsp_linker

`zwsp_linker` is a Python package designed to insert zero-width spaces into URLs within text. This is particularly useful for preventing automatic hyperlinking in markdown or other text rendering environments, while still allowing users to easily copy and paste the complete URL.

## Installation

To install `zwsp_linker`, use pip:

```bash
pip install zwsp_linker
```

## Usage

Using `zwsp_linker` is straightforward. Import the `safelink_zwsp` function and pass your text to it.

```python
from zwsp_linker import safelink_zwsp

text_with_urls = "Check out this link: http://example.com and another one https://anothersite.org."
modified_text = safelink_zwsp(text_with_urls)

print(modified_text)
# Expected output (the zero-width space is invisible):
# Check out this link: http://​example.com and another one https://​anothersite.org.
```

## How it works

The `safelink_zwsp` function uses regular expressions to find common URL schemes (like `http://` or `https://`) and inserts a zero-width space character (U+200B) immediately after the scheme. This subtle modification disrupts the automatic hyperlinking behavior of many renderers without affecting the visual appearance or the ability to copy the URL.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/zwsp_linker/issues).

## License

`zwsp_linker` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Author

Eugene Evstafev <hi@eugene.plus> - [LinkedIn](https://www.linkedin.com/in/eugene-evstafev-716669181/)

## Repository

The project is hosted on GitHub: [https://github.com/chigwell/zwsp_linker](https://github.com/chigwell/zwsp_linker)