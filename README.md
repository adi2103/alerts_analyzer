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

### Python API

```python
from src.alert_analyzer import AlertAnalyzer

# Create analyzer
analyzer = AlertAnalyzer()

# Analyze file
results = analyzer.analyze_file(
    "data/Alert_Event_Data.gz",
    dimension_name="host",
    k=5,
    alert_type="Disk Usage Alert"
)

# Print results
for entity in results:
    print(f"{entity['host_id']}: {entity['total_unhealthy_time']} seconds")
```

## Design

The Alert Analysis System uses a modular design with the following components:

1. **Models**: Data structures for alert events, alert states, and entity states
2. **Indexing**: Efficient indexing of entities by unhealthy time using SortedDict
3. **File Handling**: Reading and parsing gzipped JSON files
4. **Alert Processing**: Tracking alert lifecycle and updating entity states
5. **Query Engine**: Finding top k unhealthiest entities with optional filtering

## Project Structure

```
alerts_analyzer/
├── src/
│   ├── __init__.py
│   ├── __main__.py           # Command-line interface
│   ├── alert_analyzer.py     # Main entry point
│   ├── models.py             # Data models
│   ├── indexing/
│   │   ├── __init__.py
│   │   └── dimension_index.py # Dimension indexing
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py   # File I/O
│       └── logging_config.py # Logging setup
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_dimension_index.py
│   ├── test_alert_processor.py
│   ├── test_query_engine.py
│   ├── test_file_handler.py
│   ├── test_logging.py
│   └── test_end_to_end.py
├── requirements.txt
└── README.md
```

## Testing

Run the tests with pytest:

```
pytest
```

## Design Decisions and Trade-offs

1. **SortedDict for Ordered Access**: We use SortedDict from the sortedcontainers package to efficiently maintain entities ordered by unhealthy time. This provides O(log n) insertion and O(k) retrieval of top k entities.

2. **Multi-dimensional Indexing**: The system supports multiple dimensions (host, data center, service, etc.) through a flexible indexing mechanism. Each dimension maintains its own index of entities.

3. **Memory vs. Speed**: The system keeps all entity states in memory for fast querying, which works well for moderate-sized datasets but may need optimization for very large datasets.

4. **Alert-centric State Tracking**: We track the state of each alert and update entity states accordingly. This allows for accurate handling of overlapping alerts.

5. **Error Handling**: The system is designed to be robust against various error conditions, logging issues but continuing processing where possible.

## Future Enhancements

1. **Time Range Queries**: Support for finding unhealthy entities within specific time periods
2. **Parallel Processing**: Improved performance through parallel processing of events
3. **Additional Filtering**: More complex filtering criteria beyond alert type
4. **Visualization**: Visual representation of entity health over time
5. **Streaming Support**: Processing events in real-time from a streaming source

## License

This project is licensed under the MIT License - see the LICENSE file for details.
