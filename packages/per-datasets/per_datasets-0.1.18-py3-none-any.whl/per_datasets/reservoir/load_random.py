"""
load_random function for the reservoir module
"""

import json
import requests
import pandas as pd
from typing import Dict, Any, List, Union, Optional
from pathlib import Path

from ..talkaholic.reservoir import Reservoir
from ..utils.config import load_stored_api_key
from ..utils.display import digital_screen
from ..utils.api import get_api_config, get_headers, make_request


def load_random() -> 'Reservoir':
    """
    ## load_random
    
    Loads a random reservoir model from the reservoir datasets in the database.
    
    ### **returns**
    
    [`per_datasets.reservoir.Reservoir`]
        A Reservoir object that behaves like a pandas DataFrame with shape, to_dataframe(), and other DataFrame-like methods
        
    Raises:
        RuntimeError: If the module hasn't been initialized
    """
    try:
        # Fetch data from the API endpoint
        api_data = make_request()
        
        # Handle the actual API response structure
        # According to implementation.md, the /datasets endpoint now returns a random dataset directly
        if 'data' in api_data and 'columns' in api_data:
            data = api_data['data']
            columns = api_data['columns']
            dataset_id = api_data.get('dataset_id', 'Unknown')
            
            if len(data) == 0:
                raise ValueError("API returned dataset with no data")
            
            # Convert the first row to a dictionary for the Reservoir object
            # The data is an array of objects, so we take the first object
            first_row = data[0] if data else {}
            
            # Print the dataset ID
            print(f"Loaded dataset with ID: {dataset_id}")
            
            # Create and return Reservoir object
            return Reservoir(first_row)
        else:
            raise ValueError("API response does not contain 'data' and 'columns' fields")
        
    except Exception as e:
        if "not initialized" in str(e):
            raise e
        raise RuntimeError(f"Error loading reservoir data: {e}")