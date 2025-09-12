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
reservoir_specific = pds.reservoir.load('your_dataset_id')
print(f"Loaded specific reservoir with shape: {reservoir_specific.shape}")
# Convert to DataFrame if you need DataFrame-specific methods
df_specific = reservoir_specific.to_dataframe())

# Load all available datasets (if this function still exists)
# df_all = pds.load_all()
# print(f"Loaded all datasets with shape: {df_all.shape}")

# Get information about available datasets (if this function still exists)
# info = pds.get_dataset_info()
# print(f"Available datasets: {info}")

# Load a random reservoir object (legacy function - if this function still exists)
# reservoir = pds.load_random_reservoir()
# print(f"Reservoir object: {reservoir}")