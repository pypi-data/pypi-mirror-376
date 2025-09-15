[![PyPI version](https://badge.fury.io/py/qa_generator_ru.svg)](https://badge.fury.io/py/qa_generator_ru)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/qa_generator_ru)](https://pepy.tech/project/qa_generator_ru)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# qa_generator_ru

`qa_generator_ru` is a Python package designed to generate a large number of diverse question-answer pairs in Russian. This can be useful for creating datasets for training NLP models, populating knowledge bases, or generating practice materials.

## Installation

To install `qa_generator_ru`, use pip:

```bash
pip install qa_generator_ru
```

## Usage

Using `qa_generator_ru` is straightforward. Simply import the `generate_qa_pairs_ru` function and call it.

```python
from qa_generator_ru import generate_qa_pairs_ru
import json

# Generate QA pairs
qa_data = generate_qa_pairs_ru()

# Print the number of generated pairs
print(f"Generated {len(qa_data)} QA pairs.")

# Print the first 5 QA pairs as an example
print("\nSample QA pairs:")
print(json.dumps(qa_data[:5], indent=2, ensure_ascii=False))
```

## How it Works

The `generate_qa_pairs_ru` function creates question-answer pairs by combining predefined prompts, subjects, details, and answer templates. It randomly selects elements from these lists to construct unique questions and corresponding answers. The function generates between 2000 and 3000 QA pairs per call.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/qa_generator_ru/issues).

## License

`qa_generator_ru` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Author

**Eugene Evstafev**
LinkedIn: [![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)
Email: hi@eugene.plus
Repository: [chigwell/qa_generator_ru](https://github.com/chigwell/qa_generator_ru)