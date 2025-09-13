"""
Example usage of the per_datasets package
"""

import per_datasets as pds

# Initialize with your API key
pds.initialize('your_api_key_here')

# Load a random reservoir dataset
df_random = pds.reservoir.load_random()
print(f"Loaded random dataset with shape: {df_random.shape}")
print(f"Columns: {list(df_random.columns)}")

# Load a specific dataset by ID
df_specific = pds.reservoir.load('your_dataset_id')
print(f"Loaded specific dataset with shape: {df_specific.shape}")
print(f"Columns: {list(df_specific.columns)}")