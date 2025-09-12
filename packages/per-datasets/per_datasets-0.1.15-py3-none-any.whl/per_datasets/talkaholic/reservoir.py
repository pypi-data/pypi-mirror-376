"""
Reservoir class for the talkaholic submodule
"""

from typing import Dict, Any


class Reservoir:
    """
    A class representing a reservoir dataset
    """
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a Reservoir object with the given data
        
        Args:
            data: Dictionary containing reservoir parameters
        """
        self.data = data
    
    def __repr__(self):
        return f"Reservoir({self.data})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the reservoir data back to a dictionary"""
        return self.data
    
    def get_field(self, field_name: str, default: Any = None) -> Any:
        """
        Get any field from the original data with a default value
        
        Args:
            field_name: Name of the field to retrieve
            default: Default value if field doesn't exist
            
        Returns:
            The field value or default
        """
        return self.data.get(field_name, default)
