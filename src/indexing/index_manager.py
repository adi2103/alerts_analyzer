"""Index manager for the Alert Analysis System."""

from typing import Dict, Callable, Optional
import logging

from src.models import AlertState
from src.indexing.dimension_index import Index


class IndexManager:
    """
    Manages global indices for the Alert Analysis System.
    
    The IndexManager maintains indices for different dimensions and provides
    methods to update them when events are processed. It follows the singleton
    pattern to ensure a single global instance is used throughout the application.
    
    Time Complexity:
        - Dimension registration: O(1) - Constant time dictionary insertion
        - Index lookup: O(1) - Constant time dictionary access
        
    Space Complexity: O(D * N) where:
        - D is the number of dimensions
        - N is the number of entities across all dimensions
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of IndexManager.
        
        Returns:
            The singleton IndexManager instance
        """
        if cls._instance is None:
            cls._instance = IndexManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the IndexManager with standard dimensions."""
        # Registered dimensions for indexing/aggregation
        self.dimensions: Dict[str, Index] = {}  # dimension_name → Index
        
        # Configure logging
        self.logger = logging.getLogger("index_manager")
        
        # Register standard dimensions
        self.register_dimension("host", lambda alert_state: alert_state.tags.get("host"))
        self.register_dimension("dc", lambda alert_state: alert_state.tags.get("dc"))
        self.register_dimension("service", lambda alert_state: alert_state.tags.get("service"))
        self.register_dimension("volume", lambda alert_state: alert_state.tags.get("volume"))
    
    def register_dimension(self, dimension_name: str, extractor_func: Callable[[AlertState], Optional[str]]) -> None:
        """
        Register a new dimension for indexing and aggregation.
        
        Time Complexity: O(1) - Constant time dictionary insertion
        Space Complexity: O(1) - Stores a single new Index object
        
        Args:
            dimension_name: Name of the dimension (e.g., "host", "dc", "service")
            extractor_func: Function that extracts the entity value from an AlertState
        """
        self.dimensions[dimension_name] = Index(dimension_name, extractor_func)
        self.logger.debug(f"Registered dimension: {dimension_name}")
    
    def get_index(self, dimension_name: str) -> Index:
        """
        Get the index for a specific dimension.
        
        Time Complexity: O(1) - Constant time dictionary access
        Space Complexity: O(1) - Uses constant extra space
        
        Args:
            dimension_name: Name of the dimension to get the index for
            
        Returns:
            Index for the specified dimension
            
        Raises:
            ValueError: If the dimension is not registered
        """
        if dimension_name not in self.dimensions:
            raise ValueError(f"Dimension {dimension_name} not registered")
        return self.dimensions[dimension_name]
