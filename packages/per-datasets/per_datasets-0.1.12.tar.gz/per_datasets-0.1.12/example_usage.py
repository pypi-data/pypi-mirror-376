"""
Example usage of the per_datasets package
"""

import per_datasets as pds

# Initialize with your API key
pds.initialize('your_api_key_here')

# Load a random reservoir dataset
df_random = pds.load_random()
print(f"Loaded random dataset with shape: {df_random.shape}")
print(f"Columns: {list(df_random.columns)}")

# Load all available datasets
# df_all = pds.load_all()
# print(f"Loaded all datasets with shape: {df_all.shape}")

# Load a specific dataset by ID
# df_specific = pds.load_dataset_by_id('your_dataset_id')
# print(f"Loaded specific dataset with shape: {df_specific.shape}")

# Get information about available datasets
# info = pds.get_dataset_info()
# print(f"Available datasets: {info}")

# Load a random reservoir object (legacy function)
# reservoir = pds.load_random_reservoir()
# print(f"Reservoir object: {reservoir}")
