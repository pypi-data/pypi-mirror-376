"""
PER Datasets - A module for loading reservoir datasets
"""

__version__ = "0.1.0"

from .reservoir import initialize, load_random, load_all, load_dataset_by_id, get_dataset_info, load_random_reservoir

__all__ = ['initialize', 'load_random', 'load_all', 'load_dataset_by_id', 'get_dataset_info', 'load_random_reservoir', '__version__']
