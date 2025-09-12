[![PyPI version](https://badge.fury.io/py/llm_jsonl_converter.svg)](https://badge.fury.io/py/llm_jsonl_converter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/llm_jsonl_converter)](https://pepy.tech/project/llm_jsonl_converter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

# llm_jsonl_converter

This Python package provides functionality to convert unstructured text into JSONL (JSON Lines) format using a Large Language Model (LLM). It intelligently chunks text, prompts the LLM to generate JSON objects conforming to specified formats, and validates the output to produce a clean JSONL string.

## Features

-   **LLM-Powered Conversion:** Leverages LLMs to extract structured data from free-form text.
-   **JSONL Output:** Generates data in the widely-used JSON Lines format.
-   **Configurable Formats:** Supports defining and using custom JSONL schemas.
-   **Chunking Strategy:** Divides large texts into manageable chunks for LLM processing.
-   **Validation:** Ensures generated JSON lines conform to a specified regex pattern.
-   **Progress Indication:** Uses `tqdm` for a visual progress bar during conversion.

## Installation

To install `llm_jsonl_converter`, use pip:

```bash
pip install llm_jsonl_converter
```

## Usage

The primary function is `generate_jsonl_from_text`. You need to provide the text to convert and the name of the target JSONL format.

```python
from llm_jsonl_converter import generate_jsonl_from_text
from langchain_llm7 import ChatLLM7 # Or any other compatible BaseChatModel

# Initialize your LLM (replace with your actual LLM setup if needed)
# If llm is None, a default ChatLLM7 instance will be used.
llm_instance = ChatLLM7(
    model="gemini-2.5-flash-lite",
    base_url="https://api.llm7.io/v1"
)

# Example unstructured text
sample_text = """
John Doe is a software engineer based in New York. He works at Tech Innovations Inc.
His email is john.doe@example.com and his phone number is 123-456-7890.
He has over 5 years of experience in Python and JavaScript.
Jane Smith is a data scientist from San Francisco. She can be reached at jane.smith@company.org.
Her expertise lies in machine learning and statistical analysis.
"""

# Define the target format name (ensure this format is available via get_llm_jsonl_formats())
# For demonstration, let's assume a format named 'contacts' exists.
target_format = "contacts"

try:
    jsonl_output = generate_jsonl_from_text(
        text=sample_text,
        target_format_name=target_format,
        llm=llm_instance,
        chunk_word_size=150, # Adjust chunk size as needed
        verbose=True # Set to True for detailed logs
    )
    print(jsonl_output)
except ValueError as e:
    print(f"Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/chigwell/llm_jsonl_converter/issues).

## License

`llm_jsonl_converter` is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).

## Author

Eugene Evstafev <hi@eugene.plus>
Repository: https://github.com/chigwell/llm_jsonl_converter