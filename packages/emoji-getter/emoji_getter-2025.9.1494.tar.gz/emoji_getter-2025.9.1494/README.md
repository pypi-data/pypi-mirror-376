[![PyPI version](https://badge.fury.io/py/emoji_getter.svg)](https://badge.fury.io/py/emoji_getter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/emoji_getter)](https://pepy.tech/project/emoji_getter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# emoji_getter

`emoji_getter` is a Python package designed to extract emoji characters from a given text string. It uses a regular expression to identify and collect common emoji patterns.

## Installation

To install `emoji_getter`, use pip:

```bash
pip install emoji_getter
```

## Usage

Using `emoji_getter` is straightforward. Here's an example:

```python
from emoji_getter import emoji_extract

text_with_emojis = "Hello world! 👋 This is a test with some emojis: 😊👍🚀."
emojis = emoji_extract(text_with_emojis)
print(emojis)
```

This will output:

```
👋😊👍🚀
```

## Features

- Extracts emoji characters from text using a predefined regex.
- Returns a string containing only the found emojis.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/emoji_getter/issues).

## License

`emoji_getter` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Author

- Eugene Evstafev <hi@eugene.plus>

**Repository:** [https://github.com/chigwell/emoji_getter](https://github.com/chigwell/emoji_getter)