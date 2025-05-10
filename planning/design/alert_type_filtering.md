# Alert Type Filtering Design Extension

## Current Limitation

The current implementation has a limitation in how it handles alert type filtering. When filtering by alert type, the system:

1. Ranks entities based on their total unhealthy time across all alert types
2. Includes only entities that have at least one alert of the specified type
3. Does not recalculate unhealthy time to only include time from the specified alert type

This approach is problematic because it doesn't accurately represent the "unhealthiest" entities with respect to a specific alert type.

## Proposed Solution: Alert Type Dimension Indexing

To properly handle alert type filtering without overhauling the current implementation, we propose extending the dimension indexing system to include alert type as a filterable dimension:

```python
class AlertTypeIndex:
    """
    Maintains indices for entities by alert type.
    
    This class provides a way to efficiently query entities by alert type,
    with each alert type having its own index of entities ordered by unhealthy time.
    """
    
    def __init__(self):
        # Map of alert_type → Index
        self.alert_type_indices = {}
        
    def register_alert_type(self, alert_type: str, dimension_name: str, extractor_func: Callable):
        """Register a new alert type index."""
        if alert_type not in self.alert_type_indices:
            self.alert_type_indices[alert_type] = {}
            
        # Create index for this dimension if it doesn't exist
        if dimension_name not in self.alert_type_indices[alert_type]:
            self.alert_type_indices[alert_type][dimension_name] = Index(dimension_name, extractor_func)
            
        return self.alert_type_indices[alert_type][dimension_name]
    
    def get_index(self, alert_type: str, dimension_name: str) -> Optional[Index]:
        """Get the index for a specific alert type and dimension."""
        if alert_type not in self.alert_type_indices:
            return None
            
        return self.alert_type_indices[alert_type].get(dimension_name)
    
    def update_for_alert(self, alert_state: AlertState, start_time: datetime, end_time: datetime):
        """Update indices when an alert is resolved."""
        alert_type = alert_state.type
        
        # Skip if we're not tracking this alert type
        if alert_type not in self.alert_type_indices:
            return
            
        # Calculate unhealthy time for this alert
        unhealthy_time = (end_time - start_time).total_seconds()
        
        # Update each dimension index for this alert type
        for dimension_name, dimension_index in self.alert_type_indices[alert_type].items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue
                
            # Get or create entity state
            entity_state = dimension_index.get_entity_state(entity_value)
            old_time = dimension_index.entity_positions.get(entity_value, 0)
            
            # Update entity state
            entity_state.total_unhealthy_time += unhealthy_time
            entity_state.unhealthy_periods.append((start_time, end_time))
            entity_state.alert_type_counts[alert_type] += 1
            
            # Update position in sorted dict
            dimension_index.update_entity_position(entity_value, old_time, entity_state.total_unhealthy_time)
```

## Integration with AlertAnalyzer

The AlertAnalyzer class would be extended to use the AlertTypeIndex:

```python
class AlertAnalyzer:
    def __init__(self):
        # Existing code...
        
        # Alert type indexing
        self.alert_type_index = AlertTypeIndex()
        
        # Register standard alert types
        self.register_alert_type("Disk Usage Alert")
        self.register_alert_type("System Service Failed")
        self.register_alert_type("Time Drift Alert")
    
    def register_alert_type(self, alert_type: str):
        """Register a new alert type for tracking."""
        for dimension_name, dimension in self.dimensions.items():
            self.alert_type_index.register_alert_type(
                alert_type, 
                dimension_name, 
                dimension.extractor_func
            )
    
    def _update_indices_for_resolved_alert(self, alert_state: AlertState):
        # Existing code for updating general indices...
        
        # Also update alert type specific indices
        if alert_state.start_time and alert_state.end_time:
            self.alert_type_index.update_for_alert(
                alert_state,
                alert_state.start_time,
                alert_state.end_time
            )

    def get_top_k(self, dimension_name: str, k: int = 5, alert_type: Optional[str] = None):
        """Get top k entities by unhealthy time for a specific dimension."""
        if dimension_name not in self.dimensions:
            raise ValueError(f"Dimension {dimension_name} not registered")
        
        # If filtering by alert type, use the alert type specific index
        if alert_type:
            alert_type_dimension_index = self.alert_type_index.get_index(alert_type, dimension_name)
            if not alert_type_dimension_index:
                # No data for this alert type and dimension
                return []
                
            # Use the alert type specific index
            dimension_index = alert_type_dimension_index
        else:
            # Use the general index
            dimension_index = self.dimensions[dimension_name]
        
        # Get top k entities
        results = []
        count = 0
        processed_entities = set()
        
        for neg_time, entity_values in dimension_index.ordered_entities.items():
            for entity_value in entity_values:
                if entity_value in processed_entities:
                    continue
                    
                entity_state = dimension_index.entity_states[entity_value]
                
                results.append({
                    f"{dimension_name}_id": entity_value,
                    "total_unhealthy_time": -neg_time,
                    "alert_types": dict(entity_state.alert_type_counts)
                })
                processed_entities.add(entity_value)
                
                count += 1
                if count >= k:
                    return results
        
        return results
```

## Benefits of This Approach

1. **Modularity**: The alert type indexing is a separate component that can be added without changing the core functionality
2. **Accuracy**: Unhealthy time is calculated separately for each alert type
3. **Efficiency**: Maintains the O(k) retrieval time for top k queries
4. **Backward Compatibility**: The existing API and functionality remain unchanged
5. **Extensibility**: New alert types can be easily registered and tracked

## Implementation Strategy

Rather than overhauling the current implementation, this extension can be implemented as a new feature:

1. Add the AlertTypeIndex class
2. Extend the AlertAnalyzer to use the AlertTypeIndex
3. Update the get_top_k method to use the appropriate index based on whether alert_type is specified
4. Add tests specifically for alert type filtering accuracy

This approach allows for a clean separation of concerns and avoids disrupting the existing functionality while addressing the limitation in alert type filtering.
