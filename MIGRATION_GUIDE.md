# Migration Guide for Alert Analysis System

This guide explains the changes made to the Alert Analysis System and provides examples of how to update your code to use the new components.

## Overview of Changes

The Alert Analysis System has been refactored to separate event processing and querying concerns. The main changes are:

1. Introduction of three new components:
   - `IndexManager`: Maintains global indices for different dimensions
   - `EventProcessor`: Processes alert events and updates indices
   - `QueryEngine`: Queries indices for unhealthy entities

2. Updated command-line interface with new commands:
   - `process`: Process events from a file
   - `query`: Query top k unhealthiest entities

3. Backward compatibility:
   - The `AlertAnalyzer` class has been updated to use the new components internally
   - The existing API and command-line interface are still supported

## Using the New Components

### Processing Events

Before:
```python
from src.alert_analyzer import AlertAnalyzer

analyzer = AlertAnalyzer()
analyzer.analyze_file("data/Alert_Event_Data.gz")
```

After:
```python
from src.processors.event_processor import EventProcessor

processor = EventProcessor()
processor.process_file("data/Alert_Event_Data.gz")
```

### Querying Results

Before:
```python
from src.alert_analyzer import AlertAnalyzer

analyzer = AlertAnalyzer()
analyzer.analyze_file("data/Alert_Event_Data.gz")
results = analyzer.get_top_k("host", 5)
```

After:
```python
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine

# Process events
processor = EventProcessor()
processor.process_file("data/Alert_Event_Data.gz")

# Query results
query_engine = QueryEngine()
results = query_engine.get_top_k("host", 5)
```

### Registering Custom Dimensions

Before:
```python
from src.alert_analyzer import AlertAnalyzer

analyzer = AlertAnalyzer()
analyzer.register_dimension("custom", lambda alert_state: alert_state.tags.get("custom"))
```

After:
```python
from src.indexing.index_manager import IndexManager

index_manager = IndexManager.get_instance()
index_manager.register_dimension("custom", lambda alert_state: alert_state.tags.get("custom"))
```

## Command-Line Interface

### Processing Events

Before:
```bash
python -m src data/Alert_Event_Data.gz
```

After:
```bash
python -m src process data/Alert_Event_Data.gz
```

### Querying Results

Before:
```bash
python -m src data/Alert_Event_Data.gz --dimension host --top 5
```

After:
```bash
# First process the file
python -m src process data/Alert_Event_Data.gz

# Then query the results
python -m src query host --top 5
```

### Backward Compatibility

The old command-line interface is still supported:
```bash
python -m src data/Alert_Event_Data.gz --dimension host --top 5
```

## Alert Type Filtering

Please note that alert type filtering is not supported in this version. When specifying an alert type, a warning will be logged and results will be returned without filtering by alert type.

Before:
```python
results = analyzer.get_top_k("host", 5, alert_type="Disk Usage Alert")
```

After:
```python
# This will log a warning and return results without filtering by alert type
results = analyzer.get_top_k("host", 5, alert_type="Disk Usage Alert")
```

## Future Enhancements

The new architecture enables several future enhancements:

1. **Persistent Indices**: Store indices on disk to persist between runs
2. **File Monitoring**: Automatically process new files in a directory
3. **Advanced Querying**: Support filtering by time, dimensions, and alert type
4. **Dynamic Index Creation**: Allow creation of new indices at runtime

These enhancements will be implemented in future versions of the Alert Analysis System.
