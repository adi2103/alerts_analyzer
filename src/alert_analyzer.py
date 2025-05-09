"""Main entry point for the Alert Analysis System."""

from typing import Dict, Callable, Optional, Any, List
from datetime import datetime
import logging
from pathlib import Path

from src.models import AlertEvent, AlertState, EntityState
from src.indexing.dimension_index import Index
from src.utils.file_handler import FileHandler
from src.utils.logging_config import configure_logging, log_performance_metrics


class AlertAnalyzer:
    """
    Main class for analyzing alert events and identifying unhealthy entities.
    
    The AlertAnalyzer processes alert events, tracks alert lifecycles, and
    maintains indices for different dimensions to enable efficient querying
    of the unhealthiest entities.
    """
    
    def __init__(self):
        """Initialize an AlertAnalyzer."""
        # Alert states
        self.alert_states: Dict[str, AlertState] = {}  # alert_id → AlertState
        
        # Registered dimensions for indexing/aggregation
        self.dimensions: Dict[str, Index] = {}  # dimension_name → Index
        
        # Register standard dimensions
        self.register_dimension("host", lambda alert_state: alert_state.tags.get("host"))
        self.register_dimension("dc", lambda alert_state: alert_state.tags.get("dc"))
        self.register_dimension("service", lambda alert_state: alert_state.tags.get("service"))
        self.register_dimension("volume", lambda alert_state: alert_state.tags.get("volume"))
    
    def register_dimension(self, dimension_name: str, extractor_func: Callable[[AlertState], Optional[str]]) -> None:
        """
        Register a new dimension for indexing and aggregation.
        
        Args:
            dimension_name: Name of the dimension (e.g., "host", "dc", "service")
            extractor_func: Function that extracts the entity value from an AlertState
        """
        self.dimensions[dimension_name] = Index(dimension_name, extractor_func)
    
    def process_event(self, event: AlertEvent) -> None:
        """
        Process an alert event and update the relevant states and indices.
        
        Args:
            event: The alert event to process
        """
        # Update alert state
        alert_id = event.alert_id
        
        # Initialize alert state if needed
        if alert_id not in self.alert_states and event.state != "RSV":
            self.alert_states[alert_id] = AlertState(
                alert_id=alert_id,
                alert_type=event.type,
                tags=event.tags
            )
        
        # Skip RSV events for unknown alerts
        if alert_id not in self.alert_states:
            return
        
        alert_state = self.alert_states[alert_id]
        old_state = alert_state.current_state
        
        # Update alert state
        alert_state.update_state(event.timestamp, event.state)
        
        if event.state in ["NEW", "ACK"] and old_state is None:
            # First time seeing this alert - update entity states
            self._update_entity_states_for_new_alert(alert_state, event.timestamp)
        
        elif event.state == "RSV":
            # Alert is resolved - update entity states
            self._update_entity_states_for_resolved_alert(alert_state, event.timestamp)
            
            # Update all dimension indices
            self._update_indices_for_resolved_alert(alert_state)
            
            # We can discard the alert state now
            del self.alert_states[alert_id]
    
    def _update_entity_states_for_new_alert(self, alert_state: AlertState, timestamp: datetime) -> None:
        """
        Update entity states when a new alert is created.
        
        Args:
            alert_state: The alert state
            timestamp: When the alert was created
        """
        # Update each dimension
        for dimension_name, dimension_index in self.dimensions.items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue
            
            # Get or create entity state
            entity_state = dimension_index.get_entity_state(entity_value)
            
            # Add the alert to the entity
            entity_state.add_alert(alert_state.alert_id, alert_state.type, timestamp)
    
    def _update_entity_states_for_resolved_alert(self, alert_state: AlertState, timestamp: datetime) -> None:
        """
        Update entity states when an alert is resolved.
        
        Args:
            alert_state: The alert state
            timestamp: When the alert was resolved
        """
        # Update each dimension
        for dimension_name, dimension_index in self.dimensions.items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue
            
            # Get entity state
            if entity_value in dimension_index.entity_states:
                entity_state = dimension_index.entity_states[entity_value]
                
                # Remove the alert from the entity
                entity_state.remove_alert(alert_state.alert_id, timestamp)
    
    def _update_indices_for_resolved_alert(self, alert_state: AlertState) -> None:
        """
        Update dimension indices when an alert is resolved.
        
        Args:
            alert_state: The alert state
        """
        # Update each dimension index
        for dimension_name, dimension_index in self.dimensions.items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue
            
            # Get entity state
            if entity_value in dimension_index.entity_states:
                entity_state = dimension_index.entity_states[entity_value]
                old_time = dimension_index.entity_positions.get(entity_value, 0)
                
                # Update position in sorted dict
                self._update_entity_position(
                    dimension_index, 
                    entity_value, 
                    old_time, 
                    entity_state.total_unhealthy_time
                )
    
    def _update_entity_position(self, dimension_index: Index, entity_value: str, 
                               old_time: float, new_time: float) -> None:
        """
        Update the position of an entity in the sorted index.
        
        Args:
            dimension_index: The dimension index to update
            entity_value: Value of the entity to update
            old_time: Previous unhealthy time
            new_time: New unhealthy time
        """
        dimension_index.update_entity_position(entity_value, old_time, new_time)
    
    def get_top_k(self, dimension_name: str, k: int = 5, alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get top k entities by unhealthy time for a specific dimension.
        
        Args:
            dimension_name: Name of the dimension to query
            k: Number of entities to return
            alert_type: Optional filter for specific alert type
            
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            ValueError: If the dimension is not registered
        """
        if dimension_name not in self.dimensions:
            raise ValueError(f"Dimension {dimension_name} not registered")
        
        dimension_index = self.dimensions[dimension_name]
        
        # Apply any filters to the ordered entities
        filtered_entities = self._apply_filters(dimension_index, alert_type)
        
        # Get top k entities
        results = []
        count = 0
        
        for neg_time, entity_values in filtered_entities.items():
            for entity_value in entity_values:
                entity_state = dimension_index.entity_states[entity_value]
                
                # Skip entities that don't match the alert type filter
                if alert_type and not self._matches_alert_type(entity_value, entity_state, alert_type):
                    continue
                
                results.append({
                    f"{dimension_name}_id": entity_value,
                    "total_unhealthy_time": -neg_time,  # Convert back to positive
                    "alert_types": dict(entity_state.alert_type_counts)
                })
                
                count += 1
                if count >= k:
                    return results
        
        return results
    
    def _apply_filters(self, dimension_index: Index, alert_type: Optional[str] = None) -> Dict:
        """
        Apply filters to the ordered entities.
        
        Args:
            dimension_index: The dimension index to filter
            alert_type: Optional filter for specific alert type
            
        Returns:
            Filtered ordered entities
        """
        if not alert_type:
            # No filtering needed
            return dimension_index.ordered_entities
        
        # If filtering by alert type, we need to create a new ordered dict
        # This is because we can't efficiently filter the SortedDict directly
        filtered = {}
        
        for neg_time, entity_values in dimension_index.ordered_entities.items():
            filtered_values = set()
            
            for entity_value in entity_values:
                entity_state = dimension_index.entity_states[entity_value]
                
                if self._matches_alert_type(entity_value, entity_state, alert_type):
                    filtered_values.add(entity_value)
            
            if filtered_values:
                filtered[neg_time] = filtered_values
        
        return filtered
    
    def _matches_alert_type(self, entity_value: str, entity_state: EntityState, alert_type: str) -> bool:
        """
        Check if an entity has alerts of a specific type.
        
        Args:
            entity_value: Value of the entity to check
            entity_state: State of the entity
            alert_type: Alert type to check for
            
        Returns:
            True if the entity has alerts of the specified type, False otherwise
        """
        return alert_type in entity_state.alert_type_counts and entity_state.alert_type_counts[alert_type] > 0
    
    def analyze_file(self, file_path: str, dimension_name: str = "host", k: int = 5, 
                    alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analyze alert events from a file and return the top k unhealthiest entities.
        
        Args:
            file_path: Path to the gzipped JSON file
            dimension_name: Name of the dimension to analyze
            k: Number of entities to return
            alert_type: Optional filter for specific alert type
            
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            ValueError: If the file is not a valid gzipped JSON file or the dimension is not registered
        """
        # Configure logging
        configure_logging()
        logger = logging.getLogger("alert_analyzer")
        
        # Record start time
        start_time = datetime.now()
        
        # Create file handler
        file_handler = FileHandler(logger)
        
        # Process events
        events_processed = 0
        try:
            for event in file_handler.read_events(file_path):
                self.process_event(event)
                events_processed += 1
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
        
        # Record end time
        end_time = datetime.now()
        
        # Log performance metrics
        log_performance_metrics(start_time, end_time, events_processed, logger)
        
        # Return results
        return self.get_results(dimension_name, k, alert_type)
    
    def get_results(self, dimension_name: str = "host", k: int = 5, 
                   alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get the top k unhealthiest entities for a specific dimension.
        
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
