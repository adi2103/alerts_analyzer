"""Main entry point for the Alert Analysis System."""

from typing import Dict, Callable, Optional, Any, List
from datetime import datetime

from src.models import AlertEvent, AlertState, EntityState
from src.indexing.dimension_index import Index


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
