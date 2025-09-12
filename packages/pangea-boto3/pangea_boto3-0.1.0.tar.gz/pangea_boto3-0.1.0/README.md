# Pangea + boto3

A wrapper around boto3's Bedrock Runtime client that wraps the `converse` API
with Pangea AI Guard. Supports Python v3.10 and greater.

## Installation

```bash
pip install -U pangea-boto3
```

## Usage

```python
import os

import boto3

from pangea_boto3 import converse

# Create a Bedrock Runtime client.
brt = boto3.client("bedrock-runtime")

# Use pangea_boto3's `converse()` function instead of `brt.converse()`.
response = converse(
    # Pass the Bedrock Runtime client.
    brt,
    # Pangea arguments.
    pangea_api_key=os.getenv("PANGEA_API_KEY", ""),
    pangea_input_recipe="pangea_prompt_guard",
    pangea_output_recipe="pangea_llm_response_guard",
    # `converse()` arguments.
    modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
    messages=[{"role": "user", "content": [{"text": "Describe the purpose of a 'hello world' program in one line."}]}],
    inferenceConfig={"maxTokens": 512, "temperature": 0.5, "topP": 0.9},
    # ...
)

print(response["output"])
```
