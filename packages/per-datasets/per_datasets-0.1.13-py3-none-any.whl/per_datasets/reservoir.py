"""
Reservoir module for loading reservoir datasets from API
"""

import json
import requests
import pandas as pd
from typing import Dict, Any, List, Union, Optional
import time
import os
from pathlib import Path

from .talkaholic.reservoir import Reservoir

# Global variable to store API configuration
_API_CONFIG: Dict[str, Optional[str]] = {
    'api_key': None,
    'base_url': 'http://localhost:5000/datasets'  # Fixed internal URL
}


def _get_config_file() -> Path:
    """Get the path to the configuration file"""
    home = Path.home()
    config_dir = home / ".per_datasets"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"


def _load_stored_api_key() -> Optional[str]:
    """Load API key from global configuration"""
    config_file = _get_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('api_key')
        except (json.JSONDecodeError, IOError):
            return None
    return None




def digital_screen(text: str) -> None:
    os.system("cls" if os.name == "nt" else "clear")  # Clear terminal
    
    # Split text into lines
    lines = text.split('\n')
    
    # Find the longest line to determine width
    max_length = max(len(line) for line in lines) if lines else 0
    width = max(max_length + 4, 50)  # Minimum width of 50, plus padding
    
    # Print top border
    print("\033[1;42m" + " " * (width + 2) + "\033[0m")  # Green background
    
    # Print empty line for padding
    print("\033[1;42m" + " " + " " * width + " " + "\033[0m")
    
    # Print each line with left alignment and padding
    for line in lines:
        # Add left padding of 2 spaces and right padding to fill the container
        padded_line = "  " + line  # 2 spaces for left padding
        right_padding = width - len(padded_line)
        print("\033[1;42m" + " " + padded_line + " " * right_padding + " " + "\033[0m")
    
    # Print empty line for padding
    print("\033[1;42m" + " " + " " * width + " " + "\033[0m")
    
    # Print bottom border
    print("\033[1;42m" + " " * (width + 2) + "\033[0m")


def initialize(api_key: Optional[str] = None) -> None:
    """
    Initialize the per_datasets module with API credentials
    
    Args:
        api_key: The API key for authentication (optional if stored globally)
        
    Raises:
        ValueError: If no API key is provided and none is stored globally
    """
    global _API_CONFIG
    
    # If no API key provided, try to load from global config
    if not api_key:
        api_key = _load_stored_api_key()
        if not api_key:
            raise ValueError(
                "No API key provided and no global API key found. "
                "Please provide an API key or set one globally using: "
                "per-datasets set-key <your_api_key>"
            )
    
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")
    
    _API_CONFIG['api_key'] = api_key.strip()
    # Base URL is fixed and internal - not configurable by users
    
    # Check if the API key is valid by making a simple request
    try:
        headers = {'X-API-Key': api_key}
        response = requests.get(_API_CONFIG['base_url'], headers=headers, timeout=10)  # Increased timeout
        if response.status_code == 200:
            data = response.json()
            dataset_id = data.get('dataset_id', 'Unknown')
            # Display active status with dataset ID on separate lines
            status_text = f"STATUS: ACTIVE\nAPI KEY: pk...{api_key[-4:] if len(api_key) > 4 else api_key}\nDATASET ID: {dataset_id}"
            digital_screen(status_text)
        else:
            # Display inactive status with more details
            status_text = f"STATUS: INACTIVE\nAPI KEY: pk...{api_key[-4:] if len(api_key) > 4 else api_key}\nHTTP CODE: {response.status_code}"
            digital_screen(status_text)
            print(f"⚠️  Warning: API returned status {response.status_code}. Data loading may still work.")
    except requests.exceptions.Timeout:
        # Display inactive status for timeout
        status_text = f"STATUS: INACTIVE\nAPI KEY: pk...{api_key[-4:] if len(api_key) > 4 else api_key}\nREASON: TIMEOUT"
        digital_screen(status_text)
        print("⚠️  Warning: Connection timeout during initialization. Data loading may still work.")
    except requests.exceptions.ConnectionError:
        # Display inactive status for connection error
        status_text = f"STATUS: INACTIVE\nAPI KEY: pk...{api_key[-4:] if len(api_key) > 4 else api_key}\nREASON: CONNECTION ERROR"
        digital_screen(status_text)
        print("⚠️  Warning: Connection error during initialization. Data loading may still work.")
    except Exception as e:
        # Display inactive status for other errors
        status_text = f"STATUS: INACTIVE\nAPI KEY: pk...{api_key[-4:] if len(api_key) > 4 else api_key}\nREASON: {type(e).__name__}"
        digital_screen(status_text)
        print(f"⚠️  Warning: Error during initialization: {e}. Data loading may still work.")


def _get_headers() -> Dict[str, str]:
    """
    Get the headers for API requests
    
    Returns:
        Dict containing the required headers
        
    Raises:
        RuntimeError: If the module hasn't been initialized with an API key
    """
    if _API_CONFIG['api_key'] is None:
        raise RuntimeError("per_datasets not initialized. Call pds.initialize(apiKey='your_key') first.")
    
    return {'X-API-Key': _API_CONFIG['api_key']}


def _make_request() -> Dict[str, Any]:
    """
    Make an authenticated request to the API
    
    Returns:
        Dict containing the API response
    """
    try:
        headers = _get_headers()
        response = requests.get(_API_CONFIG['base_url'], headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to connect to API endpoint: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from API: {e}")


def load_random() -> pd.DataFrame:
    """
    Loads a random reservoir model from the API endpoint and returns as pandas DataFrame
    
    Returns:
        pandas.DataFrame: A DataFrame containing just the columns and data rows
        
    Raises:
        RuntimeError: If the module hasn't been initialized
    """
    try:
        # Fetch data from the API endpoint
        api_data = _make_request()
        
        # Handle the actual API response structure
        # According to implementation.md, the /datasets endpoint now returns a random dataset directly
        if 'data' in api_data and 'columns' in api_data:
            data = api_data['data']
            columns = api_data['columns']
            dataset_id = api_data.get('dataset_id', 'Unknown')
            
            if len(data) == 0:
                raise ValueError("API returned dataset with no data")
            
            # Create DataFrame with just the columns and data rows
            df = pd.DataFrame(data, columns=columns)
            
            # Verify the return type is a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"Expected pandas DataFrame, got {type(df)}")
            
            return df
        else:
            raise ValueError("API response does not contain 'data' and 'columns' fields")
        
    except Exception as e:
        if "not initialized" in str(e):
            raise e
        raise RuntimeError(f"Error loading reservoir data: {e}")


def load_all() -> pd.DataFrame:
    """
    Loads all reservoir datasets from the API endpoint and returns as pandas DataFrame
    
    Returns:
        pandas.DataFrame: A DataFrame containing all reservoir datasets combined
        
    Raises:
        RuntimeError: If the module hasn't been initialized
    """
    try:
        # Fetch data from the API endpoint
        api_data = _make_request()
        
        # Handle the actual API response structure
        if 'datasets' in api_data and isinstance(api_data['datasets'], list):
            datasets = api_data['datasets']
            if len(datasets) == 0:
                raise ValueError("API returned empty datasets list")
            
            # Combine all datasets into one DataFrame
            all_dataframes = []
            dataset_ids = []
            for dataset in datasets:
                if 'data' in dataset and 'columns' in dataset:
                    data = dataset['data']
                    columns = dataset['columns']
                    if len(data) > 0:
                        df = pd.DataFrame(data, columns=columns)
                        # Add dataset_id as a column for identification
                        if 'dataset_id' in dataset:
                            df['dataset_id'] = dataset['dataset_id']
                            dataset_ids.append(dataset['dataset_id'])
                        all_dataframes.append(df)
            
            if len(all_dataframes) == 0:
                raise ValueError("No valid data found in any dataset")
            
            # Print the dataset IDs
            print(f"Loaded datasets with IDs: {', '.join(dataset_ids)}")
            
            # Concatenate all DataFrames
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            return combined_df
        else:
            raise ValueError("API response does not contain 'datasets' field")
        
    except Exception as e:
        if "not initialized" in str(e):
            raise e
        raise RuntimeError(f"Error loading reservoir data: {e}")


def load_dataset_by_id(dataset_id: str) -> pd.DataFrame:
    """
    Loads a specific dataset by its ID and returns as pandas DataFrame
    
    Args:
        dataset_id: The ID of the dataset to load
        
    Returns:
        pandas.DataFrame: A DataFrame containing the specified dataset
        
    Raises:
        RuntimeError: If the module hasn't been initialized
    """
    try:
        headers = _get_headers()
        url = f"{_API_CONFIG['base_url']}/{dataset_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        api_data = response.json()
        
        # Handle the actual API response structure
        if 'data' in api_data and 'columns' in api_data:
            data = api_data['data']
            columns = api_data['columns']
            returned_dataset_id = api_data.get('dataset_id', dataset_id)
            
            if len(data) == 0:
                raise ValueError("API returned dataset with no data")
            
            # Create DataFrame with just the columns and data rows
            df = pd.DataFrame(data, columns=columns)
            
            # Print the dataset ID
            print(f"Loaded dataset with ID: {returned_dataset_id}")
            
            # Verify the return type is a pandas DataFrame
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"Expected pandas DataFrame, got {type(df)}")
            
            return df
        else:
            raise ValueError("API response does not contain 'data' and 'columns' fields")
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to connect to API endpoint: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response from API: {e}")
    except Exception as e:
        if "not initialized" in str(e):
            raise e
        raise RuntimeError(f"Error loading dataset {dataset_id}: {e}")


def get_dataset_info() -> Dict[str, Any]:
    """
    Gets information about all available datasets
    
    Returns:
        Dict containing dataset information
        
    Raises:
        RuntimeError: If the module hasn't been initialized
    """
    try:
        # Fetch data from the API endpoint
        api_data = _make_request()
        
        # Extract dataset information
        if 'datasets' in api_data and isinstance(api_data['datasets'], list):
            datasets_info = []
            dataset_ids = []
            for dataset in api_data['datasets']:
                info = {
                    'dataset_id': dataset.get('dataset_id', 'Unknown'),
                    'columns': dataset.get('columns', []),
                    'shape': dataset.get('shape', [0, 0]),
                    'row_count': len(dataset.get('data', []))
                }
                datasets_info.append(info)
                dataset_ids.append(dataset.get('dataset_id', 'Unknown'))
            
            # Print the dataset IDs
            print(f"Available datasets with IDs: {', '.join(dataset_ids)}")
            
            return {
                'count': api_data.get('count', len(datasets_info)),
                'timestamp': api_data.get('timestamp', ''),
                'datasets': datasets_info
            }
        else:
            raise ValueError("API response does not contain 'datasets' field")
        
    except Exception as e:
        if "not initialized" in str(e):
            raise e
        raise RuntimeError(f"Error loading dataset info: {e}")


def check_api_status() -> Dict[str, Any]:
    """
    Check the current API status and return detailed information
    
    Returns:
        Dict containing status information
    """
    try:
        headers = _get_headers()
        response = requests.get(_API_CONFIG['base_url'], headers=headers, timeout=10)
        
        return {
            'status': 'active' if response.status_code == 200 else 'inactive',
            'http_code': response.status_code,
            'api_key_configured': _API_CONFIG['api_key'] is not None,
            'base_url': _API_CONFIG['base_url'],
            'response_time': response.elapsed.total_seconds(),
            'data': response.json() if response.status_code == 200 else None
        }
    except requests.exceptions.Timeout:
        return {
            'status': 'timeout',
            'http_code': None,
            'api_key_configured': _API_CONFIG['api_key'] is not None,
            'base_url': _API_CONFIG['base_url'],
            'response_time': None,
            'data': None,
            'error': 'Connection timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'status': 'connection_error',
            'http_code': None,
            'api_key_configured': _API_CONFIG['api_key'] is not None,
            'base_url': _API_CONFIG['base_url'],
            'response_time': None,
            'data': None,
            'error': 'Connection error'
        }
    except Exception as e:
        return {
            'status': 'error',
            'http_code': None,
            'api_key_configured': _API_CONFIG['api_key'] is not None,
            'base_url': _API_CONFIG['base_url'],
            'response_time': None,
            'data': None,
            'error': str(e)
        }


def load_random_reservoir() -> Reservoir:
    """
    Loads a random reservoir model from the API endpoint (legacy function)
    
    Returns:
        per_datasets.talkaholic.Reservoir: A random reservoir dataset
    """
    try:
        # Get a random dataset as DataFrame first
        df = load_random()
        
        # Convert the first row to a dictionary for the Reservoir object
        if len(df) > 0:
            first_row = df.iloc[0].to_dict()
            return Reservoir(first_row)
        else:
            raise ValueError("No data available in the selected dataset")
        
    except Exception as e:
        raise RuntimeError(f"Error loading reservoir data: {e}")