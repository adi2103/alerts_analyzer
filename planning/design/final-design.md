# Alert Analysis System - Final Design Document

## 1. Overview

This document provides a detailed design for the Alert Analysis System, which processes alert event data to identify the "unhealthiest" entities based on time spent with open alerts. This implementation uses a multi-index approach with SortedDict for efficient ordered data management.

### 1.1 Problem Statement

The system analyzes an alert event stream from an internal Alert System. The data comes from a compressed file (`Alert_Event_Data.gz`) containing JSON events that represent when alerts are opened, acknowledged, or closed. The goal is to identify the top k "unhealthiest" entities, defined as those that spent the most total time with one or more open alerts.

### 1.2 Key Requirements

1. Process potentially large volumes of alert event data
2. Track alert lifecycle and calculate unhealthy time periods for multiple entity types
3. Handle various edge cases in the data
4. Support querying top k unhealthy entities by different dimensions
5. Provide a production-quality implementation with proper error handling, logging, and testing

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  File Handler   │────▶│  Event Processor│────▶│ Multi-Indexer   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│ Logging System  │◀────│  Error Handler  │◀────│  Query Engine   │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 2.2 Component Responsibilities

1. **File Handler**: Reads and parses the gzipped JSON file, handling file I/O errors
2. **Event Processor**: Processes alert events and updates alert states
3. **Multi-Indexer**: Maintains indices for different entity dimensions
4. **Query Engine**: Executes queries against the indices
5. **Error Handler**: Manages error conditions and edge cases
6. **Logging System**: Provides structured logging for monitoring and debugging

## 3. Data Structures

### 3.1 Alert Event Model

```python
class AlertEvent:
    def __init__(self, event_id, alert_id, timestamp, state, alert_type, tags):
        self.event_id = event_id
        self.alert_id = alert_id
        self.timestamp = timestamp  # datetime object
        self.state = state          # NEW, ACK, or RSV
        self.type = alert_type
        self.tags = tags

    @classmethod
    def from_json(cls, json_data):
        # Parse JSON and create AlertEvent instance
        # Handle validation and type conversion
```

### 3.2 Alert State Model

```python
class AlertState:
    def __init__(self, alert_id, alert_type, tags):
        self.alert_id = alert_id
        self.type = alert_type
        self.tags = tags
        self.current_state = None  # NEW, ACK, or RSV
        self.start_time = None     # When the alert was first opened
        self.end_time = None       # When the alert was resolved
        self.state_history = []    # List of (timestamp, state) tuples
```

### 3.3 Entity State Model

```python
class EntityState:
    def __init__(self):
        self.total_unhealthy_time = 0
        self.current_alerts = set()  # Set of active alert_ids
        self.unhealthy_start = None  # Timestamp when entity became unhealthy

        # Time series data for temporal analysis
        self.unhealthy_periods = []  # List of (start_time, end_time) tuples

        # For reporting
        self.alert_type_counts = defaultdict(int)
```

### 3.4 Multi-Index Implementation with SortedDict

```python
from sortedcontainers import SortedDict
from collections import defaultdict

class Index:
    def __init__(self, name, extractor_func):
        self.name = name
        self.extractor_func = extractor_func

        # Entity states for this dimension
        self.entity_states = {}  # entity_value → EntityState

        # SortedDict for ordered access
        # Key: -unhealthy_time (negative for reverse order)
        # Value: set of entity_values with that time
        self.ordered_entities = SortedDict()

        # Track current position of each entity in the sorted dict
        self.entity_positions = {}  # entity_value → unhealthy_time
```

### 3.5 Alert Analyzer with Multi-Index Support

```python
class AlertAnalyzer:
    def __init__(self):
        # Alert states
        self.alert_states = {}  # alert_id → AlertState

        # Registered dimensions for indexing/aggregation
        self.dimensions = {}  # dimension_name → DimensionIndex

        # Register standard dimensions
        self.register_dimension("host", lambda event: event.tags.get("host"))
        self.register_dimension("dc", lambda event: event.tags.get("dc"))
        self.register_dimension("service", lambda event: event.tags.get("service"))
        self.register_dimension("volume", lambda event: event.tags.get("volume"))

    def register_dimension(self, dimension_name, extractor_func):
        """Register a new dimension for indexing and aggregation"""
        self.dimensions[dimension_name] = Index(dimension_name, extractor_func)
```

## 4. Core Algorithms

### 4.1 Alert Lifecycle Processing

```python
def process_event(self, event):
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
    alert_state.current_state = event.state
    alert_state.state_history.append((event.timestamp, event.state))

    if event.state in ["NEW", "ACK"] and old_state is None:
        # First time seeing this alert
        alert_state.start_time = event.timestamp

    elif event.state == "RSV":
        # Alert is resolved
        alert_state.end_time = event.timestamp

        # Update all dimension indices
        self._update_indices_for_resolved_alert(alert_state)

        # We can discard the alert state now
        del self.alert_states[alert_id]
```

### 4.2 Updating Indices for Resolved Alerts

```python
def _update_indices_for_resolved_alert(self, alert_state):
    # Calculate unhealthy time for this alert
    if alert_state.start_time and alert_state.end_time:
        unhealthy_time = (alert_state.end_time - alert_state.start_time).total_seconds()
    else:
        return  # Can't calculate without both timestamps

    # Update each dimension index
    for dimension_name, dimension_index in self.dimensions.items():
        # Extract entity value for this dimension
        entity_value = dimension_index.extractor_func(alert_state)
        if not entity_value:
            continue

        # Get or create entity state
        if entity_value not in dimension_index.entity_states:
            dimension_index.entity_states[entity_value] = EntityState()
            dimension_index.entity_positions[entity_value] = 0

        entity_state = dimension_index.entity_states[entity_value]
        old_time = entity_state.total_unhealthy_time

        # Update entity state
        entity_state.total_unhealthy_time += unhealthy_time
        entity_state.unhealthy_periods.append(
            (alert_state.start_time, alert_state.end_time)
        )
        entity_state.alert_type_counts[alert_state.type] += 1

        # Update position in sorted dict
        self._update_entity_position(
            dimension_index,
            entity_value,
            old_time,
            entity_state.total_unhealthy_time
        )
```

### 4.3 Updating Entity Position in SortedDict

```python
def _update_entity_position(self, dimension_index, entity_value, old_time, new_time):
    # Remove from old position
    if old_time > 0:
        # Use negative time for reverse ordering (largest first)
        entity_set = dimension_index.ordered_entities.get(-old_time, set())
        entity_set.discard(entity_value)
        if not entity_set:
            del dimension_index.ordered_entities[-old_time]
        else:
            dimension_index.ordered_entities[-old_time] = entity_set

    # Add to new position
    if -new_time not in dimension_index.ordered_entities:
        dimension_index.ordered_entities[-new_time] = set()
    dimension_index.ordered_entities[-new_time].add(entity_value)
    dimension_index.entity_positions[entity_value] = new_time
```

### 4.4 Finding Top K Unhealthy Entities

```python
def get_top_k(self, dimension_name, k=5, alert_type=None, start_time=None, end_time=None):
    """Get top k entities by unhealthy time for a specific dimension"""
    if dimension_name not in self.dimensions:
        raise ValueError(f"Dimension {dimension_name} not registered")

    dimension_index = self.dimensions[dimension_name]

    # If time range specified, calculate unhealthy time within that range
    if start_time or end_time:
        return self._get_top_k_in_time_range(
            dimension_index, k, alert_type, start_time, end_time
        )

    # Otherwise use the pre-calculated totals
    results = []
    count = 0

    # Apply any filters to the ordered entities
    filtered_entities = self._apply_filters(dimension_index, alert_type)

    # Get top k entities
    for neg_time, entity_values in filtered_entities.items():
        for entity_value in entity_values:
            entity_state = dimension_index.entity_states[entity_value]

            results.append({
                f"{dimension_name}_id": entity_value,
                "total_unhealthy_time": -neg_time,  # Convert back to positive
                "alert_types": dict(entity_state.alert_type_counts)
            })

            count += 1
            if count >= k:
                return results

    return results
```

### 4.5 Time Range Queries

```python
def _get_top_k_in_time_range(self, dimension_index, k, alert_type, start_time, end_time):
    """Get top k entities by unhealthy time within a specific time range"""
    # Calculate unhealthy time for each entity within the time range
    entity_times = {}

    for entity_value, entity_state in dimension_index.entity_states.items():
        # Skip entities that don't match filters
        if alert_type and not self._matches_alert_type(entity_value, entity_state, alert_type):
            continue

        # Calculate unhealthy time within the specified range
        unhealthy_time = 0

        for period_start, period_end in entity_state.unhealthy_periods:
            # Skip periods outside the range
            if (start_time and period_end < start_time) or (end_time and period_start > end_time):
                continue

            # Adjust period to the specified range
            overlap_start = max(period_start, start_time) if start_time else period_start
            overlap_end = min(period_end, end_time) if end_time else period_end

            # Add the overlap duration
            unhealthy_time += (overlap_end - overlap_start).total_seconds()

        if unhealthy_time > 0:
            entity_times[entity_value] = unhealthy_time

    # Sort and return top k
    sorted_entities = sorted(entity_times.items(), key=lambda x: x[1], reverse=True)

    results = []
    for entity_value, unhealthy_time in sorted_entities[:k]:
        entity_state = dimension_index.entity_states[entity_value]
        results.append({
            f"{dimension_index.name}_id": entity_value,
            "total_unhealthy_time": unhealthy_time,
            "alert_types": dict(entity_state.alert_type_counts)
        })

    return results
```

## 5. Parallel Processing Strategy

### 5.1 Data Partitioning

The system will partition data by alert ID to enable parallel processing:

```python
def partition_by_alert(events, num_partitions):
    partitions = [[] for _ in range(num_partitions)]

    for event in events:
        partition_idx = hash(event.alert_id) % num_partitions
        partitions[partition_idx].append(event)

    return partitions
```

### 5.2 Worker Process

Each worker will:
1. Sort events by timestamp
2. Process events sequentially
3. Return alert states for its partition

```python
def process_partition(events):
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # Process events
    analyzer = AlertAnalyzer()
    for event in sorted_events:
        analyzer.process_event(event)

    return analyzer
```

### 5.3 Result Merging

```python
def merge_results(partition_analyzers):
    # Create a new analyzer for merged results
    merged_analyzer = AlertAnalyzer()

    # Register the same dimensions
    for analyzer in partition_analyzers:
        for dimension_name, dimension in analyzer.dimensions.items():
            if dimension_name not in merged_analyzer.dimensions:
                merged_analyzer.register_dimension(dimension_name, dimension.extractor_func)

    # Merge dimension indices
    for analyzer in partition_analyzers:
        for dimension_name, dimension in analyzer.dimensions.items():
            merged_dimension = merged_analyzer.dimensions[dimension_name]

            # Merge entity states
            for entity_value, entity_state in dimension.states.items():
                if entity_value not in merged_dimension.states:
                    # Copy the entire state
                    merged_dimension.states[entity_value] = entity_state

                    # Update sorted dict
                    merged_analyzer._update_entity_position(
                        merged_dimension,
                        entity_value,
                        0,
                        entity_state.total_unhealthy_time
                    )
                else:
                    # Merge state information
                    merged_entity = merged_dimension.states[entity_value]
                    old_time = merged_entity.total_unhealthy_time

                    # Add unhealthy time and periods
                    merged_entity.total_unhealthy_time += entity_state.total_unhealthy_time
                    merged_entity.unhealthy_periods.extend(entity_state.unhealthy_periods)

                    # Merge alert type counts
                    for alert_type, count in entity_state.alert_type_counts.items():
                        merged_entity.alert_type_counts[alert_type] += count

                    # Update sorted dict
                    merged_analyzer._update_entity_position(
                        merged_dimension,
                        entity_value,
                        old_time,
                        merged_entity.total_unhealthy_time
                    )

    return merged_analyzer
```

## 6. Usage Examples

### 6.1 Entities, Dimensions, and States

In our system, we have the following key concepts:

1. **Dimensions**: Categories by which we can group and analyze alerts
2. **Dimension Values**: Specific instances within a dimension
3. **Entity States**: The health state and history for each dimension value

Here are concrete examples:

#### Example 1: Host Dimension

```python
# Register the host dimension
analyzer.register_dimension("host", lambda event: event.tags.get("host"))

# Query top 5 unhealthy hosts
top_hosts = analyzer.get_top_k("host", k=5)
# Result: [
#   {"host_id": "host-84ec9fdc451b293e", "total_unhealthy_time": 7200, "alert_types": {"Disk Usage Alert": 2, "System Service Failed": 1}},
#   {"host_id": "host-29e1a7c95ccdf5b8", "total_unhealthy_time": 5400, "alert_types": {"Time Drift Alert": 1, "System Service Failed": 1}},
#   ...
# ]

# Query hosts with disk usage alerts
disk_alert_hosts = analyzer.get_top_k("host", k=3, alert_type="Disk Usage Alert")
# Result: [
#   {"host_id": "host-84ec9fdc451b293e", "total_unhealthy_time": 3600, "alert_types": {"Disk Usage Alert": 2}},
#   ...
# ]
```

#### Example 2: Data Center Dimension

```python
# Register the data center dimension
analyzer.register_dimension("dc", lambda event: event.tags.get("dc"))

# Query top 3 unhealthy data centers
top_dcs = analyzer.get_top_k("dc", k=3)
# Result: [
#   {"dc_id": "dc-293551a28c5aa121", "total_unhealthy_time": 14400, "alert_types": {"Disk Usage Alert": 5, "System Service Failed": 3}},
#   {"dc_id": "dc-4573a839ffe27bbd", "total_unhealthy_time": 10800, "alert_types": {"Time Drift Alert": 4, "System Service Failed": 2}},
#   ...
# ]

# Query data centers with time drift issues in a specific time range
time_drift_dcs = analyzer.get_top_k(
    "dc",
    k=2,
    alert_type="Time Drift Alert",
    start_time=datetime(2023, 2, 13, 0, 0),
    end_time=datetime(2023, 2, 14, 0, 0)
)
```

#### Example 3: Service Dimension

```python
# Register the service dimension
analyzer.register_dimension("service", lambda event: event.tags.get("service"))

# Query top 4 unhealthy services
top_services = analyzer.get_top_k("service", k=4)
# Result: [
#   {"service_id": "service-badf4d9ceb353a3e", "total_unhealthy_time": 5400, "alert_types": {"System Service Failed": 3}},
#   ...
# ]
```

### 6.2 Internal State Representation

Here's how the internal state would look for these examples:

```python
# Host dimension index
host_dimension = analyzer.dimensions["host"]
host_dimension.entity_states = {
    "host-84ec9fdc451b293e": EntityState(
        total_unhealthy_time=7200,
        current_alerts=set(),
        unhealthy_start=None,
        unhealthy_periods=[
            (datetime(2023, 2, 13, 10, 0), datetime(2023, 2, 13, 12, 0)),
            (datetime(2023, 2, 13, 14, 0), datetime(2023, 2, 13, 15, 0))
        ],
        alert_type_counts={"Disk Usage Alert": 2, "System Service Failed": 1}
    ),
    "host-29e1a7c95ccdf5b8": EntityState(...)
}

# Data center dimension index
dc_dimension = analyzer.dimensions["dc"]
dc_dimension.entity_states = {
    "dc-293551a28c5aa121": EntityState(
        total_unhealthy_time=14400,
        current_alerts={"alert-123"},
        unhealthy_start=datetime(2023, 2, 13, 16, 0),
        unhealthy_periods=[
            (datetime(2023, 2, 13, 8, 0), datetime(2023, 2, 13, 12, 0))
        ],
        alert_type_counts={"Disk Usage Alert": 5, "System Service Failed": 3}
    ),
    "dc-4573a839ffe27bbd": EntityState(...)
}
```

## 7. Error Handling and Logging

### 7.1 Error Categories

1. **File Processing Errors**
   - File not found
   - Permission denied
   - Corrupt gzip file

2. **JSON Parsing Errors**
   - Malformed JSON
   - Invalid schema

3. **Data Validation Errors**
   - Missing required fields
   - Invalid field values
   - Invalid timestamps

4. **Alert State Errors**
   - RSV without corresponding NEW
   - Duplicate event IDs
   - Invalid state transitions

### 7.2 Logging Strategy

```python
def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("alert_analyzer.log"),
            logging.StreamHandler()
        ]
    )

def log_event_error(event, error_type, details):
    logging.error({
        "error_type": error_type,
        "event_id": event.event_id if hasattr(event, "event_id") else None,
        "alert_id": event.alert_id if hasattr(event, "alert_id") else None,
        "details": details,
        "correlation_id": str(uuid.uuid4())
    })

def log_performance_metrics(start_time, end_time, events_processed):
    duration = end_time - start_time
    events_per_second = events_processed / duration.total_seconds()

    logging.info({
        "metric_type": "performance",
        "duration_seconds": duration.total_seconds(),
        "events_processed": events_processed,
        "events_per_second": events_per_second
    })
```

## 8. Code Structure

```
alerts_analyzer/
├── src/
│   ├── __init__.py
│   ├── alert_analyzer.py      # Main entry point
│   ├── models.py              # Data models
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── dimension_index.py # Dimension indexing
│   │   └── query_engine.py    # Query processing
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── event_processor.py # Event processing logic
│   │   └── alert_processor.py # Alert lifecycle logic
│   └── utils/
│       ├── __init__.py
│       ├── file_handler.py    # File I/O
│       └── logging_config.py  # Logging setup
├── tests/
│   ├── __init__.py
│   ├── test_dimension_index.py
│   ├── test_event_processor.py
│   ├── test_alert_processor.py
│   ├── test_file_handler.py
│   └── test_end_to_end.py
├── requirements.txt
└── README.md
```

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# Example unit test for dimension indexing
def test_dimension_index():
    # Create a dimension index
    dimension = Index("host", lambda event: event.tags.get("host"))

    # Create an alert state
    alert_state = AlertState(
        alert_id="alert1",
        alert_type="Disk Usage Alert",
        tags={"host": "host1", "dc": "dc1", "volume": "vol1"}
    )
    alert_state.start_time = datetime.fromisoformat("2023-01-01T10:00:00")
    alert_state.end_time = datetime.fromisoformat("2023-01-01T11:00:00")

    # Update the dimension index
    analyzer = AlertAnalyzer()
    analyzer._update_indices_for_resolved_alert(alert_state)

    # Verify the host was indexed correctly
    host_dimension = analyzer.dimensions["host"]
    assert "host1" in host_dimension.entity_states
    assert host_dimension.entity_states["host1"].total_unhealthy_time == 3600  # 1 hour in seconds
```

### 9.2 End-to-End Test

```python
def test_end_to_end():
    analyzer = AlertAnalyzer()
    analyzer.analyze_file("src/Alert_Event_Data.gz")

    # Test different queries
    top_hosts = analyzer.get_top_k("host", k=5)
    top_dcs = analyzer.get_top_k("dc", k=3)
    top_disk_alert_hosts = analyzer.get_top_k("host", k=5, alert_type="Disk Usage Alert")

    # Verify structure of results
    assert len(top_hosts) == 5
    assert all("host_id" in host and "total_unhealthy_time" in host for host in top_hosts)

    # Verify hosts are in descending order of unhealthy time
    times = [host["total_unhealthy_time"] for host in top_hosts]
    assert times == sorted(times, reverse=True)
```

## 10. Time and Space Complexity Analysis

### 10.1 Time Complexity

1. **Event Processing**: O(D) per event
   - O(1) to update alert state
   - O(D) to update D dimension indices

2. **Top-K Query**: O(k) for pre-calculated totals
   - Simply iterate through the SortedDict from the beginning
   - Take the first k elements

3. **Time Range Query**: O(E + n log n) where E is number of unhealthy periods and n is number of entities
   - O(E) to calculate unhealthy time in range
   - O(n log n) to sort entities by unhealthy time

4. **Parallel Processing**:
   - Partitioning: O(E) where E is the number of events
   - Processing: O(E × D) across all workers
   - Merging: O(D × N) where D is dimensions and N is entities

### 10.2 Space Complexity

1. **Alert States**: O(A) where A is number of active alerts
   - Discarded once alerts are resolved

2. **Entity States**: O(D × N + P) where:
   - D = number of dimensions
   - N = number of entities
   - P = number of unhealthy periods

3. **SortedDicts**: O(D × N)
   - One entry per entity in each dimension

4. **Total**: O(D × N + P + A)

## 11. Assumptions and Constraints

1. Multiple NEW or ACK events for the same alert_id are counted only once
2. A single RSV event closes the alert lifecycle for an alert_id
3. RSV events without corresponding NEW events are excluded
4. Events with invalid timestamps are ignored
5. For duplicate event IDs, only the first occurrence is considered
6. The time window is calculated from first NEW to first RSV
7. ACK/RSV events without a preceding NEW are dropped

## 12. Future Enhancements

1. **Performance Optimizations**:
   - Implement thread-safe SortedDict for better concurrency
   - Add bloom filters for membership testing
   - Optimize dimension extraction for faster indexing

2. **Advanced Queries**:
   - Support more complex filtering criteria
   - Add pattern detection for recurring issues
   - Implement trend analysis for entity health over time

3. **Scalability Improvements**:
   - Implement distributed processing framework
   - Add support for streaming data
   - Develop persistence layer for checkpointing

4. **Visualization and Reporting**:
   - Create dashboard for monitoring entity health
   - Add alerting for persistent unhealthy entities
   - Implement historical trend analysis

## 13. Maintaining global indices and updating indices decoupled from query engine

We need to add support for start and end time in the analyzer main entry point, so that we can make it reproducible and consume multiple data files as sequence. These will be first step towards time based filtering. I asked this because for a given file there could be alerts which saw a ACK / RSV state without a NEW state before. In this case, we want to assume the host was in unhealthy state based on the time range in the query. On the same note, we need to maintain and keep a global index running and think of our main data file as just one batch of events that are processed and consumed by the index. There could be several other files. A query on the other hand takes the entity states and finds the unhealthy time in log order using ordered data from the global indices, but also aggregations that might be pre processed there.

Currently we have alert_analyzer.py as a single entry point for both events processing and querying. What we want is to implement separation of concerns. The various Index should be globally accessible and ever evolving. Trigger to update an index will be consumption of new events or a new index creation (we will leave it for future work to create new indices). So the index updates are a hooks to event processing for the current scope. Event processor should be an running process listening to file updates or additions in data/. It can also be manually triggered but we will keep it out of scope. Lastly querying should be a manual operation like its done right now but it will not have file / data as an argument. Arguments should just be the current index name and top k args. We will leave filtering by time, dimensions and other fields like alert_type as future work.

