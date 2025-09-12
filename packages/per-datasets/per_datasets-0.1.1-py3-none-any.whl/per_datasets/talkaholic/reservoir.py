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
            data: Dictionary containing reservoir parameters (can have any structure)
        """
        self.data = data
        
        # Extract common reservoir parameters with defaults
        # Use get() with defaults to handle missing fields gracefully
        self.model = data.get('model', data.get('name', data.get('type', 'Unknown')))
        self.k = data.get('k', data.get('permeability', data.get('permeability_k', 0.0)))
        self.por = data.get('por', data.get('porosity', data.get('porosity_por', 0.0)))
        self.h = data.get('h', data.get('thickness', data.get('height', data.get('thickness_h', 0.0))))
        self.ct = data.get('ct', data.get('compressibility', data.get('total_compressibility', 0.0)))
        self.Bo = data.get('Bo', data.get('formation_volume_factor', data.get('oil_formation_volume_factor', 0.0)))
        self.visc = data.get('visc', data.get('viscosity', data.get('oil_viscosity', 0.0)))
        self.q = data.get('q', data.get('flow_rate', data.get('production_rate', 0.0)))
        self.skin = data.get('skin', data.get('skin_factor', 0.0))
        self.stor = data.get('stor', data.get('storage', data.get('wellbore_storage', 0.0)))
        self.L1 = data.get('L1', data.get('length1', data.get('dimension1', 0.0)))
        self.L2 = data.get('L2', data.get('length2', data.get('dimension2', 0.0)))
        self.L3 = data.get('L3', data.get('length3', data.get('dimension3', 0.0)))
        self.L4 = data.get('L4', data.get('length4', data.get('dimension4', 0.0)))
    
    def __repr__(self):
        return f"Reservoir(model='{self.model}', k={self.k}, por={self.por})"
    
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
