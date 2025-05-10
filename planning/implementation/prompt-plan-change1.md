# Alert Analysis System - Implementation Prompt Plan for Design Change 1

This document outlines a series of prompts for implementing the separation of event processing and querying in the Alert Analysis System. Each prompt builds incrementally on previous work, ensuring no big jumps in complexity and no orphaned code.

## Prompt 1: Create IndexManager Class

**Goal**: Create the IndexManager class that will be responsible for maintaining global indices.

```
Create the IndexManager class in src/indexing/index_manager.py that will be responsible for maintaining global indices for the Alert Analysis System.

1. Implement the IndexManager class with the following features:
   - Singleton pattern with get_instance() class method
   - Constructor that initializes dimensions dictionary
   - register_dimension() method that takes dimension_name and extractor_func
   - get_index() method that returns the index for a specific dimension

2. Register standard dimensions in the constructor:
   - "host" with lambda alert_state: alert_state.tags.get("host")
   - "dc" with lambda alert_state: alert_state.tags.get("dc")
   - "service" with lambda alert_state: alert_state.tags.get("service")
   - "volume" with lambda alert_state: alert_state.tags.get("volume")

3. Create unit tests in tests/indexing/test_index_manager.py that verify:
   - Singleton pattern works correctly
   - Dimensions can be registered
   - Standard dimensions are registered by default
   - get_index() returns the correct index or raises ValueError for unknown dimensions

Make sure to import the existing Index class from src/indexing/dimension_index.py.
```
x
## Prompt 2: Add Index Update Methods to IndexManager

**Goal**: Add methods to IndexManager for updating indices when alerts are created or resolved.

```
Extend the IndexManager class in src/indexing/index_manager.py to include methods for updating indices when alerts are created or resolved.

1. Add the following methods to IndexManager:
   - update_for_new_alert(alert_state, timestamp) - Updates indices when a new alert is created
   - update_for_resolved_alert(alert_state) - Updates indices when an alert is resolved
   - _update_entity_position(dimension_index, entity_value, old_time, new_time) - Helper method for updating entity positions in the sorted dict

2. Implement these methods based on the existing AlertAnalyzer implementation:
   - update_for_new_alert should be similar to AlertAnalyzer._update_entity_states_for_new_alert
   - update_for_resolved_alert should combine AlertAnalyzer._update_entity_states_for_resolved_alert and AlertAnalyzer._update_indices_for_resolved_alert
   - _update_entity_position should be similar to AlertAnalyzer._update_entity_position

3. Update the unit tests in tests/indexing/test_index_manager.py to verify:
   - update_for_new_alert correctly updates entity states
   - update_for_resolved_alert correctly updates entity states and indices
   - _update_entity_position correctly updates positions in the sorted dict

Make sure to handle edge cases and maintain the same behavior as the existing AlertAnalyzer implementation.
```

## Prompt 3: Create QueryEngine Class

**Goal**: Create the QueryEngine class that will be responsible for querying indices.

```
Create the QueryEngine class in src/query/query_engine.py that will be responsible for querying indices for unhealthy entities.

1. Implement the QueryEngine class with the following features:
   - Constructor that gets the IndexManager instance
   - get_top_k(dimension_name, k=5) method that returns the top k unhealthiest entities for a dimension

2. Implement the get_top_k method based on the existing AlertAnalyzer.get_top_k implementation:
   - Get the index for the specified dimension from the IndexManager
   - Iterate through the ordered entities to find the top k
   - Track processed entities to avoid duplicates
   - Format results as dictionaries with entity_id, total_unhealthy_time, and alert_types

3. Create unit tests in tests/query/test_query_engine.py that verify:
   - get_top_k returns the correct number of entities
   - Entities are sorted by unhealthy time
   - Duplicate entities are handled correctly
   - Results have the correct format

Make sure to configure logging for the QueryEngine and handle errors appropriately.
```

## Prompt 4: Create EventProcessor Class

**Goal**: Create the EventProcessor class that will be responsible for processing alert events.

```
Create the EventProcessor class in src/processors/event_processor.py that will be responsible for processing alert events and updating indices.

1. Implement the EventProcessor class with the following features:
   - Constructor that initializes alert_states dictionary and gets the IndexManager instance
   - process_event(event) method that processes an alert event and updates states and indices
   - process_file(file_path) method that processes all events in a file

2. Implement the process_event method based on the existing AlertAnalyzer.process_event implementation:
   - Update alert state based on the event
   - Handle NEW, ACK, and RSV states
   - Use the IndexManager to update indices when alerts are resolved

3. Implement the process_file method:
   - Record start time
   - Create a FileHandler
   - Process events from the file
   - Record end time and log performance metrics
   - Return the number of events processed

4. Create unit tests in tests/processors/test_event_processor.py that verify:
   - process_event correctly updates alert states
   - process_event correctly triggers index updates
   - process_file correctly processes all events in a file
   - Error handling works correctly

Make sure to configure logging for the EventProcessor and handle errors appropriately.
```

## Prompt 5: Update AlertAnalyzer for Backward Compatibility

**Goal**: Update the AlertAnalyzer class to use the new components internally for backward compatibility.

```
Update the AlertAnalyzer class in src/alert_analyzer.py to use the new components internally while maintaining backward compatibility.

1. Modify the AlertAnalyzer class:
   - Update the constructor to create EventProcessor and QueryEngine instances
   - Update analyze_file method to use the EventProcessor
   - Update get_top_k method to use the QueryEngine
   - Keep get_results as a wrapper for get_top_k

2. Add a warning in get_top_k when alert_type is specified:
   - Log a warning that alert type filtering is not supported
   - Return results without filtering by alert type

3. Update the unit tests in tests/test_alert_analyzer.py to verify:
   - analyze_file correctly processes files using the EventProcessor
   - get_top_k correctly returns results using the QueryEngine
   - get_results correctly returns results
   - A warning is logged when alert_type is specified

Make sure all existing tests still pass with the updated implementation.
```

## Prompt 6: Update Command-Line Interface

**Goal**: Update the command-line interface to support the new components.

```
Update the command-line interface in src/__main__.py to support the new components and provide separate commands for processing files and querying results.

1. Modify the command-line interface to support these commands:
   - process <file_path>: Process events from a file
   - query <dimension_name> [--top <k>]: Query top k unhealthiest entities

2. Implement the process command:
   - Create an EventProcessor
   - Process the specified file
   - Print the number of events processed

3. Implement the query command:
   - Create a QueryEngine
   - Query the top k entities for the specified dimension
   - Print the results in a readable format

4. Update the main function to parse arguments and execute the appropriate command

5. Create integration tests in tests/test_cli.py that verify:
   - The process command correctly processes files
   - The query command correctly returns results
   - Error handling works correctly

Make sure to maintain backward compatibility by supporting the existing command-line interface as well.
```

## Prompt 7: Update Results Management

**Goal**: Update the results management scripts to use the new components.

```
Update the save_results.py and list_results.py scripts to use the new components.

1. Modify save_results.py:
   - Create an EventProcessor to process the file
   - Create a QueryEngine to query results
   - Use the ResultsManager to save the results

2. Update the ResultsManager class if needed:
   - Ensure it works with the new components
   - Add any new metadata fields needed

3. Create unit tests for the updated scripts:
   - Test that save_results.py correctly saves results
   - Test that list_results.py correctly lists saved results

Make sure the scripts maintain the same functionality and output format as before.
```

## Prompt 8: Create End-to-End Tests

**Goal**: Create end-to-end tests that verify the entire system works correctly with the new components.

```
Create end-to-end tests that verify the entire Alert Analysis System works correctly with the new components.

1. Create a test in tests/test_end_to_end.py that:
   - Creates an EventProcessor and processes a sample file
   - Creates a QueryEngine and queries the top k entities
   - Verifies the results match the expected output

2. Create a test that verifies backward compatibility:
   - Creates an AlertAnalyzer
   - Calls analyze_file and get_top_k
   - Verifies the results match the expected output

3. Create a test that verifies the command-line interface:
   - Calls the process command
   - Calls the query command
   - Verifies the output matches the expected output

Make sure to use a small sample file for testing to keep the tests fast.
```

## Prompt 9: Documentation and Final Polishing

**Goal**: Update documentation and polish the implementation.

```
Update documentation and polish the implementation of the Alert Analysis System.

1. Update the README.md file:
   - Describe the new architecture
   - Explain the new components
   - Update usage examples
   - Document the new command-line interface

2. Add comprehensive docstrings to all new classes and methods:
   - IndexManager
   - QueryEngine
   - EventProcessor
   - Updated AlertAnalyzer

3. Create a migration guide for users of the existing API:
   - Explain the changes
   - Provide examples of how to update code
   - Highlight backward compatibility

4. Run linters and fix any issues:
   - Check for PEP 8 compliance
   - Fix any code style issues
   - Ensure consistent naming conventions

5. Ensure all tests pass:
   - Unit tests
   - Integration tests
   - End-to-end tests

Make sure the code is clean, well-documented, and ready for production use.
```

## Implementation Sequence

This prompt plan follows a logical progression:

1. **Core Components**: Create the IndexManager, QueryEngine, and EventProcessor classes
2. **Integration**: Update AlertAnalyzer for backward compatibility
3. **User Interface**: Update the command-line interface and results management
4. **Testing**: Create end-to-end tests
5. **Polishing**: Update documentation and polish the implementation

Each step builds directly on the previous ones, ensuring no orphaned code and maintaining a test-driven approach throughout the implementation process.
