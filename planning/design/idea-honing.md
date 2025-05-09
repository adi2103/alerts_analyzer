### INSTRUCTIONS: DO NOT MODIFY OR DELETE ###
Read rough-idea.md. Ask me one question at a time so we can develop a thorough, step-by-step spec for this idea. Each question should build on my previous answers, and our end goal is to have a detailed specification I can hand off to a developer. Let's do this iteratively and dig into every relevant detail. Remember, only one question at a time and don't repeat questions I've already answered. Update idea-honing.md as we go to track our progress.
### END INSTRUCTIONS ###

# Alert Analysis Project - Idea Honing

## Progress Tracking

### Initial Questions
1. What specific data structures would be most efficient for tracking the alert lifecycle and calculating unhealthy time periods for each host?
   - **Answer**: For finding k unhealthiest hosts with large data volumes, we'll use a host-indexed dictionary with sets of active alerts and time tracking. Each host entry will contain: total_unhealthy_time, a set of current_alerts (alert_ids), and unhealthy_start timestamp. This structure handles the alert lifecycle correctly, where multiple NEW/ACK events for the same alert_id are counted only once, and a single RSV event closes that alert.

2. How should we approach parallel processing of potentially unordered event data?
   - **Answer**: We'll partition data by host ID as the primary sharding key, with each worker processing all events for its assigned hosts. For unordered events, we'll sort by timestamp within each worker before processing. We'll use a modular design that allows for future optimizations like bloom filters, with separate components for event parsing, alert state tracking, and time calculation.

3. How should we handle edge cases in the alert data?
   - **Answer**: We'll handle edge cases as follows: RSV events without corresponding NEW events will be excluded; events with invalid timestamps will be ignored; for duplicate event IDs, we'll consider only the first occurrence; multiple NEW/ACK events for the same alert_id are allowed but only one RSV; the time window is calculated from first NEW to first RSV; ACK/RSV events without a preceding NEW are dropped. All these cases will be logged as warnings/exceptions without failing the process.

4. How should we structure the output report for top k unhealthiest hosts?
   - **Answer**: The output will include: host ID, total unhealthy time, set of alert types observed for each host, and count of each alert type. Additionally, we'll support querying top k unhealthy hosts by specific alert types (e.g., disk usage, time drift) by maintaining separate tracking for each alert type.

5. How should we make the system extensible for many alert types?
   - **Answer**: We'll use a dynamic type registry instead of hardcoding alert types, implement type-agnostic core processing logic, use flexible data structures with defaultdict for automatic handling of new types, and adopt a configuration-driven approach that allows defining alert types without code changes.

6. What error handling and logging strategy should we implement?
   - **Answer**: We'll log file processing errors, JSON deserialization errors (with line numbers), missing field errors, incorrect field literals, and alert state warnings for corner cases. We'll also track performance metrics (processing rate, memory usage), data quality metrics, and use structured logging in JSON format with correlation IDs.

7. How should we structure the code to make it testable?
   - **Answer**: We'll use a simple, readable structure with proper separation of concerns: models for data structures, processors for core logic, and utilities for file handling and logging. We'll implement unit tests for key components (event processing, host analysis) and one end-to-end test using the provided data file.

## Data Structure Analysis and Comparison

After extensive analysis, we've compared several data structures for efficiently tracking and querying unhealthy hosts:

### 1. Concurrent Hash Tables with Ordered Indices
- **Time Complexity**: O(1) for updates, O(n log n) for sorting (only when needed)
- **Space Complexity**: O(H + A) where H = hosts, A = active alerts
- **Parallelism**: Excellent - naturally shardable by host ID
- **Simplicity**: High - uses familiar data structures
- **Used in**: Prometheus, many monitoring systems
- **Key advantage**: Flexible and easy to understand/modify

### 2. Skip Lists
- **Time Complexity**: O(log n) for search/insert/delete
- **Space Complexity**: O(n log n) expected
- **Parallelism**: Good - lock-free implementations available
- **Simplicity**: Moderate - probabilistic nature adds complexity
- **Used in**: Redis sorted sets, Java's ConcurrentSkipListMap
- **Key advantage**: Good concurrent access patterns

### 3. LSM Trees
- **Time Complexity**: O(1) amortized for writes, O(log n) for reads
- **Space Complexity**: O(n) with good compression
- **Parallelism**: Excellent for writes, moderate for reads
- **Simplicity**: Low - complex compaction strategies
- **Used in**: Time-series databases, Cassandra, RocksDB
- **Key advantage**: Optimized for high write throughput

### 4. Red-Black Trees
- **Time Complexity**: O(log n) for operations
- **Space Complexity**: O(n)
- **Parallelism**: Poor - complex rebalancing operations
- **Simplicity**: Moderate - complex balancing rules
- **Used in**: Many in-memory databases
- **Key advantage**: Guaranteed O(log n) performance

### 5. Time-Bucketed Aggregation
- **Time Complexity**: O(1) for updates, O(B) for queries where B = buckets
- **Space Complexity**: O(H × B + A)
- **Parallelism**: Good - can partition by time and host
- **Simplicity**: Moderate
- **Used in**: Time-series monitoring systems
- **Key advantage**: Efficient temporal analysis

## Recent Discussions and Brainstorming

### Modular Multi-Index Design

We've evolved our design to a more flexible and extensible approach that can handle various types of queries beyond just ranking hosts by unhealthy time. This modular multi-index design:

1. Supports multiple indexing dimensions (host, data center, service, volume, etc.)
2. Allows dynamic registration of new dimensions
3. Maintains efficient ordered indices for each registered dimension

```python
class AlertAnalyzer:
    def __init__(self):
        # Primary data store - all events by entity ID
        self.entities = {}  # entity_id → EntityState
        
        # Registered dimensions for indexing/aggregation
        self.dimensions = {}  # dimension_name → DimensionIndex
        
        # Register standard dimensions
        self.register_dimension("host", lambda event: event.tags.get("host"))
        self.register_dimension("dc", lambda event: event.tags.get("dc"))
        self.register_dimension("service", lambda event: event.tags.get("service"))
        self.register_dimension("volume", lambda event: event.tags.get("volume"))
```

### Example Queries Supported

```python
# Top 5 unhealthy hosts
analyzer.get_top_k("host", k=5)

# Top 3 data centers with most unhealthy time
analyzer.get_top_k("dc", k=3)

# Top 5 volumes with disk usage alerts
analyzer.get_top_k("volume", k=5, filter_criteria={"alert_type": "Disk Usage Alert"})

# Top services in a specific data center
analyzer.get_top_k("service", k=5, filter_criteria={"dc": "dc-123"})
```

### Additional Requirements

1. **Time Range Queries**:
   - We need to support queries for specific time ranges
   - This requires tracking unhealthy periods with timestamps
   - Time buckets could be useful but shouldn't be the only approach
   - Solution: Maintain a timeline of state changes per entity that can be queried by time range

2. **Handling Partially Ordered Events**:
   - Events are mostly ordered by time but may have race conditions
   - Need an index and data structure that benefits from partial ordering
   - Solution: Use a combination of buffering and sorting for small batches of events
   - Leverage the natural ordering in the data to minimize sorting overhead

### Proposed Time Range Query Implementation

```python
class DimensionIndex:
    # ... existing code ...
    
    def get_top_k_in_time_range(self, start_time, end_time, k=5, filter_criteria=None):
        """Get top k entities by unhealthy time within a specific time range"""
        # Calculate unhealthy time for each entity within the time range
        entity_times = {}
        
        for entity_id, state in self.entity_states.items():
            # Calculate unhealthy time within the specified range
            unhealthy_time = state.calculate_unhealthy_time_in_range(start_time, end_time)
            if unhealthy_time > 0:
                entity_times[entity_id] = unhealthy_time
        
        # Apply filters
        if filter_criteria:
            entity_times = self._apply_time_range_filters(entity_times, filter_criteria)
        
        # Sort and return top k
        sorted_entities = sorted(entity_times.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for entity_id, unhealthy_time in sorted_entities[:k]:
            results.append({
                f"{self.name}_id": entity_id,
                "total_unhealthy_time": unhealthy_time,
                "alert_types": dict(self.entity_states[entity_id].alert_type_counts)
            })
        
        return results
```

### Handling Partially Ordered Events

```python
class EventProcessor:
    def __init__(self, buffer_size=1000):
        self.buffer = []
        self.buffer_size = buffer_size
    
    def process_events(self, event_stream, analyzer):
        """Process events with efficient handling of partial ordering"""
        # Buffer for batch processing
        for event in event_stream:
            self.buffer.append(event)
            
            # When buffer is full, sort and process
            if len(self.buffer) >= self.buffer_size:
                self._process_buffer(analyzer)
        
        # Process any remaining events
        if self.buffer:
            self._process_buffer(analyzer)
    
    def _process_buffer(self, analyzer):
        # Sort buffer by timestamp (should be mostly ordered already)
        self.buffer.sort(key=lambda e: e.timestamp)
        
        # Process events in order
        for event in self.buffer:
            analyzer.process_event(event)
        
        # Clear buffer
        self.buffer = []
```

### Final Design Decisions

After evaluating various data structures and approaches, we've decided to use:

1. **SortedDict from sortedcontainers** as our primary ordered data structure:
   - Internally uses Python dicts, lists, and Timsort
   - Efficient for partially ordered data
   - Simple API and good performance characteristics
   - Well-maintained Python library

2. **Alert-centric state tracking**:
   - States will be a property of an alert (alert-id → state mapping)
   - State information can be discarded once an alert reaches RSV
   - Each event can update the state of its associated alert-id

3. **Multi-dimensional indexing**:
   - Support multiple indices based on alert fields (type, host, tags, etc.)
   - Each index maintains its own SortedDict for efficient top-k queries
   - Indices are updated after each event is processed

4. **Time-based aggregation**:
   - Track time buckets, time series, and total unhealthy time
   - Update aggregations after each event is processed
   - Support time range queries efficiently

This approach provides a flexible, efficient, and extensible solution for alert analysis that can handle various query patterns while maintaining good performance characteristics.