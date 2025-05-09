# Alert Analysis System - Implementation Prompt Plan

This document outlines a series of prompts for implementing the Alert Analysis System in a test-driven manner. Each prompt builds incrementally on previous work, ensuring no big jumps in complexity and no orphaned code.

## Prompt 1: Project Setup and Basic Models

**Goal**: Set up the project structure and implement the basic data models.

```
Create a Python project structure for the Alert Analysis System with the following components:
1. Set up the directory structure as outlined in the design document
2. Create a requirements.txt file with necessary dependencies
3. Implement the basic data models (AlertEvent and AlertState) in src/models.py
4. Write unit tests for these models in tests/test_models.py
5. Include proper docstrings and type hints

The models should follow these specifications:
- AlertEvent: Represents an alert event with event_id, alert_id, timestamp, state, type, and tags
- AlertState: Tracks the state of an alert with alert_id, type, tags, current_state, start_time, end_time, and state_history

Ensure all tests pass and the code follows PEP 8 standards.
```

## Prompt 2: File Handling and JSON Parsing

**Goal**: Implement file handling and JSON parsing functionality.

```
Building on the previous implementation, create the file handling and JSON parsing components:

1. Implement a FileHandler class in src/utils/file_handler.py that:
   - Reads and decompresses the gzipped JSON file
   - Parses each line into an AlertEvent object
   - Handles file I/O errors gracefully

2. Write unit tests in tests/test_file_handler.py that:
   - Test successful file reading
   - Test handling of invalid files
   - Test parsing of valid and invalid JSON

3. Create a small sample test file for testing purposes

Use the AlertEvent model from the previous step. Ensure proper error handling and logging for file not found, permission denied, corrupt gzip files, and malformed JSON.
```

## Prompt 3: Entity State Model and Basic Index

**Goal**: Implement the EntityState model and basic Index structure.

```
Building on the previous implementation, create the EntityState model and basic Index structure:

1. Implement the EntityState class in src/models.py that:
   - Tracks total_unhealthy_time
   - Maintains a set of current_alerts
   - Records unhealthy_start timestamp
   - Stores unhealthy_periods as a list of (start_time, end_time) tuples
   - Keeps count of alert types in alert_type_counts

2. Implement a basic Index class in src/indexing/dimension_index.py that:
   - Initializes with a name and extractor_function
   - Maintains a dictionary of entity_states (entity_value → EntityState)
   - Includes a SortedDict for ordered access to entities by unhealthy time
   - Tracks entity positions in the sorted structure

3. Write unit tests for both classes in tests/test_models.py and tests/test_dimension_index.py

Use the sortedcontainers.SortedDict for the ordered index implementation. Ensure proper type hints and documentation.
```

## Prompt 4: Alert Lifecycle Processing

**Goal**: Implement the core alert lifecycle processing logic.

```
Building on the previous implementation, create the alert lifecycle processing components:

1. Implement the core of the AlertAnalyzer class in src/alert_analyzer.py that:
   - Maintains a dictionary of alert_states (alert_id → AlertState)
   - Registers dimensions with extractor functions
   - Processes events to update alert states
   - Updates indices when alerts are resolved

2. Implement these key methods:
   - register_dimension(dimension_name, extractor_func)
   - process_event(event)
   - _update_indices_for_resolved_alert(alert_state)
   - _update_entity_position(index, entity_value, old_time, new_time)

3. Write unit tests in tests/test_alert_processor.py that verify:
   - Alert state transitions (NEW → ACK → RSV)
   - Index updates when alerts are resolved
   - Handling of edge cases (duplicate events, missing states)

Focus on the core alert lifecycle logic without implementing query functionality yet. Ensure all tests pass and the code handles the edge cases specified in the design document.
```

## Prompt 5: Basic Query Engine Implementation

**Goal**: Implement the basic query engine for finding top k unhealthy hosts.

```
Building on the previous implementation, create the basic query engine components:

1. Extend the AlertAnalyzer class in src/alert_analyzer.py to add:
   - get_top_k(dimension_name, k=5, alert_type=None)
   - _apply_filters(index, alert_type)
   - _matches_alert_type(entity_value, entity_state, alert_type)

2. Write unit tests in tests/test_query_engine.py that verify:
   - Basic top-k queries work correctly
   - Filtering by alert type works
   - Edge cases are handled properly

Focus specifically on the core requirement of finding the top 5 unhealthiest hosts, with optional filtering by alert type. The implementation should efficiently retrieve the top k entities based on the specified criteria.
```

## Prompt 6: Error Handling and Logging

**Goal**: Implement basic error handling and logging.

```
Building on the previous implementation, add basic error handling and logging:

1. Implement a logging configuration in src/utils/logging_config.py that:
   - Sets up structured logging with appropriate formatters
   - Configures file and console handlers
   - Defines different log levels for different types of messages

2. Add these logging functions:
   - log_event_error(event, error_type, details)
   - log_performance_metrics(start_time, end_time, events_processed)

3. Integrate error handling and logging for the most critical components:
   - File processing errors
   - JSON parsing errors
   - Data validation errors
   - Alert state errors

4. Write unit tests in tests/test_logging.py that verify:
   - Errors are logged correctly
   - Performance metrics are recorded

Focus on essential error handling and logging that directly impacts the core functionality of finding unhealthy hosts.
```

## Prompt 7: End-to-End Integration

**Goal**: Create an end-to-end integration that ties all components together.

```
Building on the previous implementation, create an end-to-end integration:

1. Implement the main entry point in src/alert_analyzer.py that:
   - Provides a simple API for analyzing alert data
   - Ties together all the components (file handling, processing, querying)

2. Add these methods to the AlertAnalyzer class:
   - analyze_file(file_path, k=5)
   - get_results(dimension_name, k=5, alert_type=None)

3. Write an end-to-end test in tests/test_end_to_end.py that:
   - Processes the provided Alert_Event_Data.gz file
   - Verifies the top 5 unhealthiest hosts
   - Tests filtering by alert type

4. Create a simple command-line interface in src/__main__.py that:
   - Accepts file path and basic query parameters
   - Outputs results in a readable format

Ensure all components work together seamlessly and that the end-to-end test passes with the actual data file.
```

## Prompt 8: Documentation and Final Polishing

**Goal**: Finalize documentation and polish the implementation.

```
Building on the previous implementation, finalize the documentation and polish the code:

1. Add comprehensive docstrings to all classes and methods following Google or NumPy style

2. Create a detailed README.md that explains:
   - Project purpose and functionality
   - Installation instructions
   - Usage examples
   - Design decisions and trade-offs

3. Ensure code quality by:
   - Running a linter and fixing any issues
   - Checking for consistent code style
   - Reviewing error handling for completeness

4. Add a simple performance test that measures:
   - Processing time for the provided data file
   - Memory usage during processing

5. Ensure all tests pass and the code is ready for production use

The final implementation should be well-documented, clean, and ready for use by production engineers to find the top 5 unhealthiest hosts.
```

## Prompt 9: Future Work Documentation

**Goal**: Document future enhancements and extensions.

```
Create a document outlining future work and enhancements for the Alert Analysis System:

1. Write a future_work.md file that describes these potential enhancements:
   - Time range queries for finding unhealthy hosts within specific time periods
   - Parallel processing for handling larger datasets
   - Support for more complex filtering criteria
   - Alert severity weighting
   - Visualization capabilities
   - Additional dimensions beyond hosts (e.g., services, data centers)

2. For each enhancement, include:
   - A brief description of the feature
   - The potential benefits and use cases
   - High-level implementation approach
   - Any dependencies or prerequisites

This document will serve as a roadmap for future development of the Alert Analysis System beyond the core requirement of finding the top 5 unhealthiest hosts.
```

## Future Extension Prompts (Not For Immediate Implementation)

### Extension Prompt 1: Time Range Queries

```
Extend the Alert Analysis System to support time range queries:

1. Implement the _get_top_k_in_time_range method in the AlertAnalyzer class that:
   - Calculates unhealthy time for each entity within a specified time range
   - Filters entities based on alert type if specified
   - Returns the top k entities sorted by unhealthy time in the range

2. Update the get_top_k method to accept start_time and end_time parameters

3. Write unit tests that verify:
   - Time range queries return correct results
   - Overlapping periods are handled correctly
   - Edge cases (empty ranges, future ranges) are handled properly

This extension will allow users to analyze host health within specific time periods rather than just overall.
```

### Extension Prompt 2: Parallel Processing

```
Extend the Alert Analysis System to support parallel processing:

1. Implement these functions in src/processors/event_processor.py:
   - partition_by_alert(events, num_partitions)
   - process_partition(events)
   - merge_results(partition_analyzers)

2. Add an analyze_file_parallel method to the AlertAnalyzer class that:
   - Partitions the data by alert ID
   - Processes partitions in parallel using multiple workers
   - Merges the results to find the global top k entities

3. Write unit tests that verify:
   - Parallel processing produces the same results as sequential processing
   - Performance improves with multiple workers (for large datasets)

This extension will improve performance for large datasets by utilizing multiple CPU cores.
```

### Extension Prompt 3: Additional Dimensions and Complex Filtering

```
Extend the Alert Analysis System to support additional dimensions and complex filtering:

1. Enhance the AlertAnalyzer class to:
   - Register and use multiple dimensions (dc, service, volume)
   - Support cross-dimension queries and filtering

2. Implement a more flexible filtering mechanism that:
   - Accepts complex criteria with multiple conditions
   - Supports filtering across different dimensions
   - Allows for advanced query patterns

3. Write unit tests that verify:
   - Queries across different dimensions work correctly
   - Complex filtering produces expected results

This extension will provide more powerful analysis capabilities beyond just host-level metrics.
```

### Extension Prompt 4: Visualization

```
Add visualization capabilities to the Alert Analysis System:

1. Create a visualization module that:
   - Generates charts of unhealthy time by entity
   - Shows trends over time for selected entities
   - Visualizes distribution of alert types

2. Implement integration with common plotting libraries (matplotlib, seaborn)

3. Add options to export visualizations in various formats

This extension will help users better understand patterns and trends in the alert data through visual representations.
```

## Implementation Sequence

This prompt plan follows a logical progression:

1. **Foundation**: Project setup and basic models
2. **Data Ingestion**: File handling and parsing
3. **Core Data Structures**: Entity state and indexing
4. **Core Logic**: Alert lifecycle processing
5. **Analysis**: Basic query engine implementation
6. **Robustness**: Error handling and logging
7. **Integration**: End-to-end functionality
8. **Polishing**: Documentation and final touches
9. **Future Planning**: Documentation of future enhancements

Each step builds directly on the previous ones, ensuring no orphaned code and maintaining a test-driven approach throughout the implementation process.
