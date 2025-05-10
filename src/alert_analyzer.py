"""Main entry point for the Alert Analysis System."""

from typing import Dict, Callable, Optional, Any, List
from datetime import datetime
import logging

from src.models import AlertEvent, AlertState
from src.indexing.dimension_index import Index
from src.utils.file_handler import FileHandler
from src.utils.logging_config import configure_logging, log_performance_metrics
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine


class AlertAnalyzer:
    """
    Main class for analyzing alert events and identifying unhealthy entities.
    
    This class is maintained for backward compatibility and uses the new
    components (EventProcessor and QueryEngine) internally.
    
    Time Complexity:
        - Event processing: O(D) per event where D is the number of dimensions
        - Top-k query: O(k) where k is the number of results requested
        - File analysis: O(E * D + k) where E is the number of events
        
    Space Complexity: O(A + D * N) where:
        - A is the number of active alerts at any given time
        - D is the number of dimensions
        - N is the number of entities across all dimensions
    """
    
    def __init__(self):
        """Initialize an AlertAnalyzer."""
        # Create EventProcessor and QueryEngine instances
        self.processor = EventProcessor()
        self.query_engine = QueryEngine()
        
        # Configure logging
        configure_logging()
        self.logger = logging.getLogger("alert_analyzer")

    def register_dimension(self,
                           dimension_name: str,
                           extractor_func: Callable[[AlertState],
                                                    Optional[str]]) -> None:
        """
        Register a new dimension for indexing and aggregation.
        
        This method is maintained for backward compatibility and delegates to
        the IndexManager via the EventProcessor.
        
        Time Complexity: O(1) - Constant time dictionary insertion
        Space Complexity: O(1) - Stores a single new Index object
        
        Args:
            dimension_name: Name of the dimension (e.g., "host", "dc", "service")
            extractor_func: Function that extracts the entity value from an AlertState
        """
        self.processor.index_manager.register_dimension(dimension_name, extractor_func)
    
    def process_event(self, event: AlertEvent) -> None:
        """
        Process an alert event and update the relevant states and indices.
        
        This method is maintained for backward compatibility and delegates to
        the EventProcessor.
        
        Time Complexity: O(D) where D is the number of dimensions
        Space Complexity: O(1) - Uses constant extra space
        
        Args:
            event: The alert event to process
        """
        self.processor.process_event(event)

    def get_top_k(self, dimension_name: str, k: int = 5,
                  alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get top k entities by unhealthy time for a specific dimension.
        
        This method is maintained for backward compatibility and delegates to
        the QueryEngine.
        
        Time Complexity: O(k) - Linear in the number of results requested
        Space Complexity: O(k) - Stores k result entities
        
        Args:
            dimension_name: Name of the dimension to query
            k: Number of entities to return
            alert_type: Optional filter for specific alert type (Note: This parameter is kept for API compatibility
                       but alert type filtering is not supported in this version)
                       
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            ValueError: If the dimension is not registered
        """
        if alert_type:
            self.logger.warning(
                "Alert type filtering is not supported in this version. "
                "Returning results without filtering by alert type."
            )
        
        return self.query_engine.get_top_k(dimension_name, k)

    def analyze_file(self,
                     file_path: str,
                     dimension_name: str = "host",
                     k: int = 5,
                     alert_type: Optional[str] = None) -> List[Dict[str,
                                                                    Any]]:
        """
        Analyze alert events from a file and return the top k unhealthiest entities.
        
        This method is maintained for backward compatibility and delegates to
        the EventProcessor and QueryEngine.
        
        Time Complexity: O(E * D + k) where:
            - E is the number of events in the file
            - D is the number of dimensions
            - k is the number of results requested
            
        Space Complexity: O(A + D * N) where:
            - A is the number of active alerts at any given time
            - D is the number of dimensions
            - N is the number of entities across all dimensions
            
        Args:
            file_path: Path to the gzipped JSON file
            dimension_name: Name of the dimension to analyze
            k: Number of entities to return
            alert_type: Optional filter for specific alert type (Note: This parameter is kept for API compatibility
                       but alert type filtering is not supported in this version)
                       
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            ValueError: If the file is not a valid gzipped JSON file or the dimension is not registered
        """
        # Process events
        self.processor.process_file(file_path)
        
        # Return results
        return self.get_results(dimension_name, k, alert_type)
    
    def get_results(self, dimension_name: str = "host", k: int = 5,
                    alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the top k unhealthiest entities for a specific dimension.
        
        This method is maintained for backward compatibility and delegates to
        get_top_k.
        
        Time Complexity: O(k) - Linear in the number of results requested
        Space Complexity: O(k) - Stores k result entities
        
        Args:
            dimension_name: Name of the dimension to query
            k: Number of entities to return
            alert_type: Optional filter for specific alert type
            
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            ValueError: If the dimension is not registered
        """
        return self.get_top_k(dimension_name, k, alert_type)
