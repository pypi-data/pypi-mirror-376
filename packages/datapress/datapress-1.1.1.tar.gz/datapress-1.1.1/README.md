# DataPress Python Client

A Python client library for interacting with the [DataPress API](https://datapress.com/docs/api).

## Installation

```bash
pip install datapress
```

## How to Use

Set your API credentials as environment variables:

```bash
export DATAPRESS_API_KEY="your-api-key"
export DATAPRESS_URL="https://your-datapress-instance.com"
```

### Basic Usage

```python
from datapress import DataPressClient

# Initialize client
client = DataPressClient()

# Verify authentication
user_info = client.whoami()
print(f"Logged in as: {user_info['title']}")

# Get a dataset
dataset = client.get_dataset("ab12x")
print(f"Dataset: {dataset['title']}")
```

### Renaming a Dataset

```python
# Rename a dataset using patch operations
patch = [{"op": "replace", "path": "/title", "value": "New Dataset Name"}]
result = client.patch_dataset("ab12x", patch)
print(f"Dataset renamed to: {result['dataset']['title']}")
```

### Adding a File

```python
# Upload a new file to a dataset
result = client.upload_file(
    dataset_id="ab12x",
    file_path="data/sales.csv",
    # Optional parameters:
    title="Sales Data",
    description="Monthly sales figures",
    order=1,
    timeframe={"from": "2024-01", "to": "2025-04"}
)
print(f"File uploaded with ID: {result['resource_id']}")
```

### Replacing a File

```python
# Replace an existing file
result = client.upload_file(
    dataset_id="ab12x",
    file_path="data/updated_spending.csv",
    # Optional parameters:
    resource_id="xyz",  # ID of existing file to replace
    title="Updated Spending Data"
)
print(f"File replaced: {result['resource_id']}")
```
