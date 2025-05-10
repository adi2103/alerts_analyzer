# Alert Analysis System

A system for analyzing alert event data to identify the "unhealthiest" entities, defined as those that spent the most total time with one or more open alerts.

## Overview

The Alert Analysis System processes alert event data from a compressed file containing JSON events that represent when alerts are opened, acknowledged, or closed. It tracks the lifecycle of alerts and calculates the total time each entity (host, data center, service, etc.) spent in an unhealthy state.

## Features

- Process alert events from gzipped JSON files
- Track alert lifecycle (NEW → ACK → RSV)
- Calculate unhealthy time for different entity dimensions
- Find top k unhealthiest entities
- Filter results by alert type
- Handle various edge cases in the data
- Provide detailed logging and error handling
- Save and manage analysis results with query metadata
- Query server for persistent in-memory indices

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/alerts_analyzer.git
cd alerts_analyzer
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

### Command-line Interface

#### Processing Events

```
python -m src process <file_path>
```

This command processes events from a file and updates the global indices.

#### Querying Results

```
python -m src query <dimension_name> [options]
```

Options:
- `--top`, `-k`: Number of entities to return (default: 5)
- `--output`, `-o`: Output file path (default: stdout)
- `--format`, `-f`: Output format (json or text, default: text)

Example:
```
python -m src query host --top 10
```

#### Legacy Mode (Backward Compatibility)

```
python -m src <file_path> [options]
```

Options:
- `--dimension`, `-d`: Dimension to analyze (default: host)
- `--top`, `-k`: Number of entities to return (default: 5)
- `--alert-type`, `-t`: Filter by alert type
- `--output`, `-o`: Output file path (default: stdout)
- `--format`, `-f`: Output format (json or text, default: text)

Example:
```
python -m src data/Alert_Event_Data.gz --dimension host --top 10 --alert-type "Disk Usage Alert"
```

#### Saving Results

```
python save_results.py <file_path> [options]
```

Options:
- `--dimension`, `-d`: Dimension to analyze (default: host)
- `--top`, `-k`: Number of entities to return (default: 5)
- `--alert-type`, `-t`: Filter by alert type

Example:
```
python save_results.py data/Alert_Event_Data.gz --dimension dc --top 3
```

#### Listing Saved Results

```
python list_results.py
```

This will display all saved analysis results with their query parameters.

### Query Server

The system includes a simple server that can maintain indices in memory and respond to queries from multiple clients.

#### Starting the Server

```
python query_server.py <file_path> [options]
```

Options:
- `--host`: Host to bind to (default: localhost)
- `--port`: Port to bind to (default: 5000)

Example:
```
python query_server.py data/Alert_Event_Data.gz --port 5000
```

#### Querying the Server

```
python query_client.py <dimension_name> [options]
```

Options:
- `--top`, `-k`: Number of entities to return (default: 5)
- `--server`: Server URL (default: http://localhost:5000)
- `--format`, `-f`: Output format (json or text, default: text)

Example:
```
python query_client.py host --top 10 --server http://localhost:5000
```

### Python API

```python
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine
from src.utils.results_manager import ResultsManager

# Process events
processor = EventProcessor()
processor.process_file("data/Alert_Event_Data.gz")

# Query results
query_engine = QueryEngine()
results = query_engine.get_top_k("host", 5)

# Print results
for entity in results:
    print(f"{entity['host_id']}: {entity['total_unhealthy_time']} seconds")

# Save results with metadata
results_manager = ResultsManager()
filename, saved_results = results_manager.save_results(
    results,
    "data/Alert_Event_Data.gz",
    "host",
    5,
    None
)

# List all saved results
all_results = results_manager.list_results()
for result in all_results:
    print(f"{result['filename']}: {result['dimension']} - {result['top_k']} results")

# Load a specific result
loaded_result = results_manager.load_results(filename)
```

#### Backward Compatibility

The `AlertAnalyzer` class is still available for backward compatibility:

```python
from src.alert_analyzer import AlertAnalyzer

# Create analyzer
analyzer = AlertAnalyzer()

# Analyze file
results = analyzer.analyze_file(
    "data/Alert_Event_Data.gz",
    dimension_name="host",
    k=5,
    alert_type="Disk Usage Alert"  # Note: Alert type filtering is not supported in this version
)
```

## Architecture

The Alert Analysis System uses a modular design with the following components:

1. **IndexManager**: Maintains global indices for different dimensions
2. **EventProcessor**: Processes alert events and updates indices
3. **QueryEngine**: Queries indices for unhealthy entities
4. **AlertAnalyzer**: Provides backward compatibility with the old API

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

## Project Structure

```
alerts_analyzer/
├── src/
│   ├── __init__.py
│   ├── __main__.py           # Command-line interface
│   ├── alert_analyzer.py     # Backward compatibility
│   ├── models.py             # Data models
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── dimension_index.py # Dimension indexing
│   │   └── index_manager.py   # Index management
│   ├── processors/
│   │   ├── __init__.py
│   │   └── event_processor.py # Event processing
│   ├── query/
│   │   ├── __init__.py
│   │   └── query_engine.py    # Query processing
│   ├── server/
│   │   ├── __init__.py
│   │   └── index_server.py    # Query server
│   ├── client/
│   │   ├── __init__.py
│   │   └── query_client.py    # Query client
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py   # File I/O
│       ├── logging_config.py # Logging setup
│       └── results_manager.py # Results management
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_dimension_index.py
│   ├── test_index_manager.py
│   ├── test_event_processor.py
│   ├── test_query_engine.py
│   ├── test_alert_analyzer.py
│   ├── test_file_handler.py
│   ├── test_results_manager.py
│   ├── test_cli.py
│   ├── test_end_to_end.py
│   ├── server/
│   │   ├── __init__.py
│   │   └── test_index_server.py
│   └── client/
│       ├── __init__.py
│       └── test_query_client.py
├── results/                  # Directory for saved analysis results
├── save_results.py           # Script to save analysis results
├── list_results.py           # Script to list saved results
├── query_server.py           # Script to start the query server
├── query_client.py           # Script to query the server
├── MIGRATION_GUIDE.md        # Guide for migrating to the new API
├── requirements.txt
└── README.md
```

## Testing

Run the tests with pytest:

```
pytest
```

## Known Limitations

1. **Alert Type Filtering**: Alert type filtering is not supported in this version. When specifying an alert type, a warning will be logged and results will be returned without filtering by alert type.

2. **Persistence**: Indices are not persisted between runs. They are built in memory each time events are processed.

## Future Enhancements

1. **Persistent Indices**: Store indices on disk to persist between runs
2. **File Monitoring**: Automatically process new files in a directory
3. **Advanced Querying**: Support filtering by time, dimensions, and alert type
4. **Dynamic Index Creation**: Allow creation of new indices at runtime

## License

This project is licensed under the MIT License - see the LICENSE file for details.
