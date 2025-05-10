# Design Change: Separation of Event Processing and Querying

## Overview

This document outlines a design change to implement separation of concerns in the Alert Analysis System. Currently, `alert_analyzer.py` serves as a single entry point for both event processing and querying. The proposed change will separate these responsibilities to allow for:

1. Global, ever-evolving indices that persist across multiple event processing runs
2. Event processing that can be triggered by file updates or manually
3. Querying that operates on the current state of indices without requiring file processing

## Current Architecture

```
┌─────────────────┐
│                 │
│  AlertAnalyzer  │◄────── File Input
│                 │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│                 │
│     Indices     │
│                 │
└───────┬─────────┘
        │
        ▼
┌─────────────────┐
│                 │
│     Results     │
│                 │
└─────────────────┘
```

## Proposed Architecture

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│ EventProcessor  │────►│  IndexManager   │
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
       ▲                         │
       │                         │
       │                         ▼
File Input               ┌─────────────────┐
                         │                 │
                         │  QueryEngine    │◄────── Query Input
                         │                 │
                         └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │     Results     │
                         │                 │
                         └─────────────────┘
```

## Component Responsibilities

### 1. IndexManager

The `IndexManager` will be responsible for:
- Maintaining global indices for different dimensions
- Providing methods to update indices when events are processed
- Persisting indices between runs (future enhancement)
- Providing access to indices for querying

```python
class IndexManager:
    """
    Manages global indices for the Alert Analysis System.
    
    The IndexManager maintains indices for different dimensions and provides
    methods to update them when events are processed.
    """
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance of IndexManager."""
        if cls._instance is None:
            cls._instance = IndexManager()
        return cls._instance
    
    def __init__(self):
        """Initialize the IndexManager."""
        # Registered dimensions for indexing/aggregation
        self.dimensions = {}  # dimension_name → Index
        
        # Register standard dimensions
        self.register_dimension("host", lambda alert_state: alert_state.tags.get("host"))
        self.register_dimension("dc", lambda alert_state: alert_state.tags.get("dc"))
        self.register_dimension("service", lambda alert_state: alert_state.tags.get("service"))
        self.register_dimension("volume", lambda alert_state: alert_state.tags.get("volume"))
    
    def register_dimension(self, dimension_name, extractor_func):
        """Register a new dimension for indexing and aggregation."""
        self.dimensions[dimension_name] = Index(dimension_name, extractor_func)
    
    def update_for_new_alert(self, alert_state, timestamp):
        """Update indices when a new alert is created."""
        # Implementation similar to AlertAnalyzer._update_entity_states_for_new_alert
        
    def update_for_resolved_alert(self, alert_state, timestamp):
        """Update indices when an alert is resolved."""
        # Implementation similar to AlertAnalyzer._update_entity_states_for_resolved_alert
        # and AlertAnalyzer._update_indices_for_resolved_alert combined
    
    def get_index(self, dimension_name):
        """Get the index for a specific dimension."""
        if dimension_name not in self.dimensions:
            raise ValueError(f"Dimension {dimension_name} not registered")
        return self.dimensions[dimension_name]
```

### 2. EventProcessor

The `EventProcessor` will be responsible for:
- Processing alert events from files
- Updating alert states
- Triggering index updates via the IndexManager
- Handling file monitoring (future enhancement)

```python
class EventProcessor:
    """
    Processes alert events and updates indices.
    
    The EventProcessor reads alert events from files and updates
    the global indices via the IndexManager.
    """
    
    def __init__(self):
        """Initialize an EventProcessor."""
        # Alert states
        self.alert_states = {}  # alert_id → AlertState
        
        # Get the index manager
        self.index_manager = IndexManager.get_instance()
        
        # Configure logging
        configure_logging()
        self.logger = logging.getLogger("alert_processor")
    
    def process_event(self, event):
        """Process an alert event and update the relevant states and indices."""
        # Implementation similar to AlertAnalyzer.process_event
        # but using self.index_manager for index updates
        
    def process_file(self, file_path):
        """Process alert events from a file."""
        # Record start time
        start_time = datetime.now()
        
        # Create file handler
        file_handler = FileHandler(self.logger)
        
        # Process events
        events_processed = 0
        try:
            for event in file_handler.read_events(file_path):
                self.process_event(event)
                events_processed += 1
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            raise
        
        # Record end time
        end_time = datetime.now()
        
        # Log performance metrics
        log_performance_metrics(start_time, end_time, events_processed, self.logger)
        
        return events_processed
```

### 3. QueryEngine

The `QueryEngine` will be responsible for:
- Querying indices for top k unhealthiest entities
- Formatting and returning results
- Supporting various query parameters (future enhancement)

```python
class QueryEngine:
    """
    Queries indices for unhealthy entities.
    
    The QueryEngine provides methods to query the global indices
    for the top k unhealthiest entities.
    """
    
    def __init__(self):
        """Initialize a QueryEngine."""
        # Get the index manager
        self.index_manager = IndexManager.get_instance()
        
        # Configure logging
        configure_logging()
        self.logger = logging.getLogger("query_engine")
    
    def get_top_k(self, dimension_name, k=5):
        """
        Get top k entities by unhealthy time for a specific dimension.
        
        Args:
            dimension_name: Name of the dimension to query
            k: Number of entities to return
            
        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time
            
        Raises:
            ValueError: If the dimension is not registered
        """
        # Get the index for the specified dimension
        index = self.index_manager.get_index(dimension_name)
        
        # Get top k entities
        results = []
        count = 0
        processed_entities = set()  # Track entities we've already processed
        
        for neg_time, entity_values in index.ordered_entities.items():
            for entity_value in entity_values:
                # Skip entities we've already processed (avoid duplicates)
                if entity_value in processed_entities:
                    continue
                
                entity_state = index.entity_states[entity_value]
                
                # Add to results and mark as processed
                results.append({
                    f"{dimension_name}_id": entity_value,
                    "total_unhealthy_time": -neg_time,  # Convert back to positive
                    "alert_types": dict(entity_state.alert_type_counts)
                })
                processed_entities.add(entity_value)
                
                count += 1
                if count >= k:
                    return results
        
        return results
```

## Implementation Plan

### Phase 1: Create New Components

1. Create `src/indexing/index_manager.py` with the `IndexManager` class
2. Create `src/processors/event_processor.py` with the `EventProcessor` class
3. Create `src/query/query_engine.py` with the `QueryEngine` class

### Phase 2: Refactor Existing Code

1. Move index-related code from `AlertAnalyzer` to `IndexManager`
2. Move event processing code from `AlertAnalyzer` to `EventProcessor`
3. Move query-related code from `AlertAnalyzer` to `QueryEngine`
4. Update `AlertAnalyzer` to use the new components (for backward compatibility)

### Phase 3: Update Entry Points

1. Create a new command-line interface in `src/__main__.py` that supports:
   - Processing files: `python -m src process <file_path>`
   - Querying: `python -m src query <dimension_name> [--top <k>]`
2. Update `save_results.py` and `list_results.py` to use the new components

### Phase 4: Add Tests

1. Create unit tests for `IndexManager`
2. Create unit tests for `EventProcessor`
3. Create unit tests for `QueryEngine`
4. Update existing tests to use the new components

## Future Enhancements

1. **Persistent Indices**: Store indices on disk to persist between runs
2. **File Monitoring**: Automatically process new files in a directory
3. **Advanced Querying**: Support filtering by time, dimensions, and alert type
4. **Dynamic Index Creation**: Allow creation of new indices at runtime

## API Changes

### Current API

```python
analyzer = AlertAnalyzer()
analyzer.analyze_file("data/Alert_Event_Data.gz")
results = analyzer.get_top_k("host", 5)
```

### New API

```python
# Process events
processor = EventProcessor()
processor.process_file("data/Alert_Event_Data.gz")

# Query results
query_engine = QueryEngine()
results = query_engine.get_top_k("host", 5)
```

## Backward Compatibility

To maintain backward compatibility, the `AlertAnalyzer` class will be updated to use the new components internally:

```python
class AlertAnalyzer:
    """
    Main class for analyzing alert events and identifying unhealthy entities.
    
    This class is maintained for backward compatibility and uses the new
    components internally.
    """
    
    def __init__(self):
        """Initialize an AlertAnalyzer."""
        self.processor = EventProcessor()
        self.query_engine = QueryEngine()
    
    def analyze_file(self, file_path, dimension_name="host", k=5, alert_type=None):
        """
        Analyze alert events from a file and return the top k unhealthiest entities.
        """
        self.processor.process_file(file_path)
        return self.get_results(dimension_name, k, alert_type)
    
    def get_top_k(self, dimension_name, k=5, alert_type=None):
        """
        Get top k entities by unhealthy time for a specific dimension.
        """
        if alert_type:
            logging.getLogger("alert_analyzer").warning(
                "Alert type filtering is not supported in this version. "
                "Returning results without filtering by alert type."
            )
        
        return self.query_engine.get_top_k(dimension_name, k)
    
    def get_results(self, dimension_name="host", k=5, alert_type=None):
        """
        Get the top k unhealthiest entities for a specific dimension.
        """
        return self.get_top_k(dimension_name, k, alert_type)
```

## Conclusion

This design change will improve the modularity and maintainability of the Alert Analysis System by separating event processing and querying concerns. It will also enable future enhancements such as persistent indices, file monitoring, and advanced querying capabilities.
