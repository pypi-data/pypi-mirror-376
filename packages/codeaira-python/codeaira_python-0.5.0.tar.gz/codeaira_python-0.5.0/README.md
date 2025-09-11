# CodeAira Python Client

[![PyPI version](https://badge.fury.io/py/codeaira-python.svg)](https://badge.fury.io/py/codeaira-python)
[![Python Version](https://img.shields.io/pypi/pyversions/codeaira-python.svg)](https://pypi.org/project/codeaira-python)
[![License](https://img.shields.io/pypi/l/codeaira-python.svg)](https://pypi.org/project/codeaira-python)

A Python client library for the CodeAira API.

## Installation

You can install `codeaira-python` from PyPI:

```bash
pip install codeaira-python
```

## Configuration

The client requires your CodeAira API key and the API base URL. It loads these from environment variables. You can either export them in your shell or create a `.env` file in your project's root directory.

**Example `.env` file:**

```
CODEAIRA_API_KEY="your_api_key_here"
CODEAIRA_BASE_URL="codeaira-api-base-url here"
```

If these variables are not found, a `ConfigurationError` will be raised.

## Usage

Here is a basic example of how to use the `CodeAiraClient` to get a text completion.

```python
from codeaira import CodeAiraClient, DataOnlyResponse, FullCompletionResponse
from codeaira.exceptions import CodeAiraException

# The client automatically loads configuration from environment variables
# or a .env file.
client = CodeAiraClient()

try:
    # Example 1: Get only the completion data (default behavior)
    response: DataOnlyResponse = client.complete_text(
        model_name="gemini-2.5-flash",
        prompt="Write a short story about a robot who discovers music."
    )
    print("Completion Data Only:")
    print(response.data)

    print("-" * 20)

    # Example 2: Get the full API response object
    full_response: FullCompletionResponse = client.complete_text(
        model_name="gemini-2.5-flash",
        prompt="Translate 'hello world' to French.",
        response_only=False
    )
    print("Full API Response:")
    # .model_dump_json() is a pydantic method
    print(full_response.model_dump_json(indent=2))

except CodeAiraException as e:
    print(f"An error occurred: {e}")
```

## API Reference

### `CodeAiraClient`

The main client for interacting with the CodeAira API.

#### `__init__()`

Initializes the client. It reads `CODEAIRA_API_KEY` and `CODEAIRA_BASE_URL` from the environment.
- **Raises**: `ConfigurationError` if the required environment variables are not set.

#### `complete_text(model_name, prompt, context=None, app_id=None, response_only=True)`

Sends a completion request to the CodeAira API.

- **Parameters**:
    - `model_name` (str): The name of the model to use for the completion. A list of valid models can be found in `src/codeaira/models.py`.
    - `prompt` (str): The prompt to send to the model.
    - `context` (str, optional): Additional context for the completion. Defaults to `None`.
    - `app_id` (str, optional): An identifier for your application. Defaults to `None`.
    - `response_only` (bool): If `True` (default), returns a `DataOnlyResponse` object containing just the completion text. If `False`, returns a `FullCompletionResponse` object with all details from the API response.

- **Returns**: `DataOnlyResponse` or `FullCompletionResponse` depending on the `response_only` flag.

- **Raises**:
    - `ValidationError`: If the request data fails Pydantic validation.
    - `NetworkError`: For network-related issues (e.g., connection problems).
    - `APIError`: If the CodeAira API returns an error response.

### Models

The library uses Pydantic models for data validation and serialization.

- `CodeAiraRequest`: The model for the request sent to the API.
- `DataOnlyResponse`: A simplified response model containing only the `data` (the completion string).
- `FullCompletionResponse`: The complete response model, including `success`, `data`, `log_id`, `thread_id`, `location`, and `error`.

### Exceptions

Custom exceptions are raised for specific error conditions.

- `CodeAiraException`: The base exception for all library-specific errors.
- `ConfigurationError`: For issues with configuration, like a missing API key.
- `APIError`: When the API returns an error (e.g., status code 4xx or 5xx). Contains `status_code` and `error_message` attributes.
- `NetworkError`: For network-related problems during the request.
- `ValidationError`: For Pydantic validation errors on request or response data.

## Development

To set up for development:

1.  Clone the repository.
2.  Create and activate a virtual environment.
3.  Install the package in editable mode with development dependencies:
    ```bash
    pip install -e ".[dev]"
    ```
4.  Create a `.env` file with your credentials for running tests and examples.

## License

This project is licensed under the terms of the LICENSE file.