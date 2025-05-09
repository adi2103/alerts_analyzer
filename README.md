# Alert Analysis System

A system for analyzing alert event data to identify the "unhealthiest" hosts, defined as those that spent the most total time with one or more open alerts.

## Overview

The Alert Analysis System processes alert event data from a compressed file containing JSON events that represent when alerts are opened, acknowledged, or closed. It tracks the lifecycle of alerts and calculates the total time each host spent in an unhealthy state.

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

*Coming soon*

## Development

### Running Tests

```
pytest
```

## Project Structure

```
alerts_analyzer/
├── src/
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── alert_analyzer.py      # Main entry point
│   ├── indexing/
│   │   ├── __init__.py
│   │   └── dimension_index.py # Dimension indexing
│   ├── processors/
│   │   ├── __init__.py
│   │   └── event_processor.py # Event processing logic
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py    # File I/O
│       └── logging_config.py  # Logging setup
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   └── ...
├── requirements.txt
└── README.md
```
