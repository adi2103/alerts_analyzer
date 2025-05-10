# Alert Analysis System

A system for analyzing alert event data to identify the "unhealthiest" entities, defined as those that spent the most total time with one or more open alerts.

## Overview

The Alert Analysis System processes alert event data from a compressed file containing JSON events that represent when alerts are opened, acknowledged, or closed. It tracks the lifecycle of alerts and calculates the total time each entity (host, data center, service, etc.) spent in an unhealthy state.

## Features

- Process alert events from gzipped JSON files
- Track alert lifecycle (NEW → ACK → RSV)
- Calculate unhealthy time for different entity dimensions
- Find top k unhealthiest entities
- Handle various edge cases in the data
- Provide detailed logging and error handling
- Save and manage analysis results with query metadata
- Server-client architecture for persistent in-memory indices

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/alerts_analyzer.git
cd alerts_analyzer
```

2. Set up a Python virtual environment:

This project requires Python 3.12.4. Using a virtual environment ensures that the project's dependencies don't conflict with your other Python projects.

```bash
# Create a virtual environment
python3.12 -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Verify Python version
python --version  # Should output Python 3.12.4
```

If you don't have Python 3.12.4 installed, you can install it using:
- macOS: `brew install python@3.12` (using Homebrew)
- Linux: Use your distribution's package manager or pyenv
- Windows: Download from the [official Python website](https://www.python.org/downloads/)

3. Install dependencies:
```
pip install -r requirements.txt
```

4. When you're done working on the project, deactivate the virtual environment:
```
deactivate
```

## Usage

The Alert Analysis System uses a server-client architecture:

### Server

Start the server to process data files and serve queries:

```
python query_server.py <file_path> [<file_path2> ...] [options]
```

Options:
- `--host`: Host to bind to (default: localhost)
- `--port`: Port to bind to (default: 8080)
- `--debug`: Run in debug mode

Example:
```
python query_server.py data/Alert_Event_Data.gz
```

The server can process multiple data files:
```
python query_server.py data/Alert_Event_Data.gz data/More_Alert_Data.gz
```

### Client

Use the client to query the server and manage results:

#### Querying the Server

```
python query_client.py query <dimension_name> [options]
```

Options:
- `--top`, `-k`: Number of entities to return (default: 5)
- `--server`: Server URL (default: http://localhost:8080)
- `--format`, `-f`: Output format (json or text, default: text)
- `--save`, `-s`: Save the query results

Example:
```
python query_client.py query host --top 5 --save
```

#### Listing Saved Results

```
python query_client.py list [options]
```

Options:
- `--format`, `-f`: Output format (json or text, default: text)

Example:
```
python query_client.py list
```

#### Loading Saved Results

```
python query_client.py load <filename> [options]
```

Options:
- `--format`, `-f`: Output format (json or text, default: text)

Example:
```
python query_client.py load query_results_20230214_120000.json
```



## Architecture

The Alert Analysis System uses a server-client architecture with the following components:

1. **IndexManager**: Maintains global indices for different dimensions
2. **EventProcessor**: Processes alert events and updates indices
3. **IndexServer**: Serves queries via HTTP API
4. **QueryClient**: Queries the server and manages results

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│ query_server.py │────►│  IndexServer    │
│                 │     │                 │
└─────────────────┘     └────────┬────────┘
       ▲                         │
       │                         │
       │                         ▼
File Input               ┌─────────────────┐
                         │                 │
                         │  EventProcessor │
                         │                 │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │                 │
                         │  IndexManager   │
                         │                 │
                         └─────────────────┘
                                  ▲
                                  │
                                  │
                         ┌─────────────────┐
                         │                 │
                         │ query_client.py │◄────── User Input
                         │                 │
                         └─────────────────┘
```

## Project Structure

```
alerts_analyzer/
├── src/
│   ├── __init__.py
│   ├── models.py             # Data models
│   ├── dimension_index.py    # Dimension indexing
│   ├── index_manager.py      # Index management
│   ├── event_processor.py    # Event processing
│   ├── query_engine.py       # Query processing
│   ├── index_server.py       # Query server
│   ├── query_client.py       # Query client
│   ├── file_handler.py       # File I/O
│   ├── logging_config.py     # Logging setup
│   └── results_manager.py    # Results management
├── tests/
│   ├── __init__.py
│   ├── test_models.py        # Tests for data models
│   ├── test_dimension_index.py # Tests for dimension indexing
│   ├── test_file_handler.py  # Tests for file handling
│   └── test_index_server.py  # Tests for server functionality
├── results/                  # Directory for saved analysis results
├── query_server.py           # Script to start the query server
├── query_client.py           # Script to query the server
├── requirements.txt
└── README.md
```

## Testing

The Alert Analysis System includes a comprehensive test suite using pytest. The tests cover the core functionality of the system, including data models, file handling, dimension indexing, and server functionality.

### Test Coverage

Current test coverage is at 49% overall for the codebase:

```
Name                     Stmts   Miss  Cover
--------------------------------------------
src/__init__.py              0      0   100%
src/dimension_index.py      39      3    92%
src/event_processor.py      41     26    37%
src/file_handler.py         60     12    80%
src/index_manager.py        45     19    58%
src/index_server.py         99     45    55%
src/logging_config.py       47     18    62%
src/models.py               88      3    97%
src/query_client.py        132    132     0%
src/query_engine.py         32     22    31%
src/results_manager.py      34     34     0%
--------------------------------------------
TOTAL                      617    314    49%
```

Well-tested modules include:
- models.py (97% coverage): Core data models for alerts and entities
- dimension_index.py (92% coverage): Efficient indexing for entity dimensions
- file_handler.py (80% coverage): File I/O and JSON parsing

To run the tests:

```
pytest
```

For coverage report:

```
pytest --cov=src tests/
```

## Development Notes

This project was developed over approximately 4 hours, with significant effort focused on:

1. **Design Phase**: Creating a robust architecture before implementation, focusing on data structures and algorithms for efficient entity tracking and querying.

2. **Core Implementation**: The most significant independent contributions were in:
   - src/models.py: Comprehensive data models with proper validation and error handling
   - src/dimension_index.py: Efficient indexing using SortedDict for O(k) retrieval of top entities
   - src/event_processor.py: Processing alert events and updating entity states
   - src/index_manager.py: Managing global indices for different dimensions

3. **Testing & Quality Assurance**: Extensive testing, logging, and debugging to ensure correctness and reliability.

4. **Assumptions**: There are some assumptions made in lieu of prototyping:
   - If the file has a ACK or RSV state for an alert then the alert is counted in but the unhealthy time is only included only the from first NEW / ACK state seen in the file and not from the first timestamp in the file.
   - If the file has a NEW or ACK but not RSV state for an alert, then the alert is counted but the unhealthy time is not included in the host's total unhealthy time. This is because the unhealthy time update happens only when RSV is observed for an alert
   - Multiple NEW or ACK events for the same alert_id are counted only once
   - A single RSV event closes the alert lifecycle for an alert_id
   - RSV events without corresponding NEW events are excluded
   - Events with invalid timestamps are ignored
   - Apart from the file boundary, the time window is calculated from first NEW to first RSV


## Known Limitations

1. **Alert Type Filtering**: Alert type filtering is not supported in this version. As noted in the conversation summary, the original implementation was flawed as it ranked entities by total unhealthy time across all alert types instead of only considering time from the specified alert type.

2. **Persistence**: Indices are not persisted between server restarts. They are built in memory each time the server starts.

3. **Duplicate Entities**: The system was previously affected by a bug where duplicate entities could appear in query results. This has been fixed by tracking processed entities in the query engine.

## Future Enhancements

1. **Alert Type Filtering**: Implement proper alert type filtering by tracking unhealthy time separately for each alert type, as outlined in the design extension document.

2. **Persistent Indices**: Store indices on disk to persist between server restarts.

3. **File Monitoring**: Automatically process new files in a directory.

4. **Advanced Querying**: Support filtering by time, dimensions, and alert type.

5. **Dynamic Index Updates**: Allow creation and updates of new indices at server runtime.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
