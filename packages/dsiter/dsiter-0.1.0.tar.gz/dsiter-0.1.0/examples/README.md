# Examples

This directory contains example files demonstrating how to use the `dsiter` library.

## Files

- `datasets.yml` - Example configuration file showing how to configure datasets from HuggingFace and local files
- `example.py` - Simple example script showing how to iterate over datasets using the library

## Running the Example

1. Make sure you have the `dsiter` library installed:
   ```bash
   pip install dsiter
   ```

2. Run the example script:
   ```bash
   python example.py
   ```

## Configuration

The `datasets.yml` file contains various commented examples of different dataset configurations:
- HuggingFace datasets with specific columns
- Local CSV/TSV files
- Parquet files
- Different column selections

Uncomment the datasets you want to use by removing the `#` symbols.
