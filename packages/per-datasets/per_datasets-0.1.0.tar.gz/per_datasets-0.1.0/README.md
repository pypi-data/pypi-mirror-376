# PER Datasets

A Python package for loading reservoir datasets from API endpoints.

## Installation

```bash
pip install per_datasets
```

## Usage

```python
import per_datasets as pds

# Initialize with your API key
pds.initialize('your_api_key_here')

# Load a random reservoir dataset
random_dataset = pds.load_random()

# Load all available datasets
all_datasets = pds.load_all()

# Load a specific dataset by ID
specific_dataset = pds.load_dataset_by_id('dataset_id')

# Get information about available datasets
info = pds.get_dataset_info()
```

## Dependencies

- requests>=2.25.1
- pandas>=1.3.0

## License

MIT
