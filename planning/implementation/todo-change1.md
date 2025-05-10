# Alert Analysis System - Implementation Checklist for Design Change 1

This checklist tracks progress on implementing the separation of event processing and querying in the Alert Analysis System according to the prompt plan.

## Prompt 1: Create IndexManager Class
- [x] Create src/indexing/index_manager.py file
- [x] Implement IndexManager class with singleton pattern
- [x] Add get_instance() class method
- [x] Implement constructor with dimensions dictionary
- [x] Add register_dimension() method
- [x] Add get_index() method
- [x] Register standard dimensions (host, dc, service, volume)
- [x] Create tests/indexing/test_index_manager.py
- [x] Write tests for singleton pattern
- [x] Write tests for dimension registration
- [x] Write tests for standard dimensions
- [x] Write tests for get_index() method

## Prompt 2: Add Index Update Methods to IndexManager
- [ ] Add update_for_new_alert() method
- [ ] Add update_for_resolved_alert() method
- [ ] Add _update_entity_position() helper method
- [ ] Update tests to verify update_for_new_alert()
- [ ] Update tests to verify update_for_resolved_alert()
- [ ] Update tests to verify _update_entity_position()
- [ ] Ensure edge cases are handled
- [ ] Verify behavior matches existing AlertAnalyzer implementation

## Prompt 3: Create QueryEngine Class
- [ ] Create src/query/query_engine.py file
- [ ] Implement QueryEngine class
- [ ] Add constructor that gets IndexManager instance
- [ ] Implement get_top_k() method
- [ ] Add logic to track processed entities
- [ ] Format results correctly
- [ ] Create tests/query/test_query_engine.py
- [ ] Write tests for get_top_k() method
- [ ] Write tests for entity sorting
- [ ] Write tests for duplicate entity handling
- [ ] Write tests for result format
- [ ] Configure logging for QueryEngine

## Prompt 4: Create EventProcessor Class
- [ ] Create src/processors/event_processor.py file
- [ ] Implement EventProcessor class
- [ ] Add constructor with alert_states dictionary
- [ ] Get IndexManager instance in constructor
- [ ] Implement process_event() method
- [ ] Handle NEW, ACK, and RSV states
- [ ] Implement process_file() method
- [ ] Add performance metrics logging
- [ ] Create tests/processors/test_event_processor.py
- [ ] Write tests for process_event() method
- [ ] Write tests for process_file() method
- [ ] Write tests for error handling
- [ ] Configure logging for EventProcessor

## Prompt 5: Update AlertAnalyzer for Backward Compatibility
- [ ] Update AlertAnalyzer constructor to use new components
- [ ] Update analyze_file() method to use EventProcessor
- [ ] Update get_top_k() method to use QueryEngine
- [ ] Keep get_results() as a wrapper for get_top_k()
- [ ] Add warning for alert_type filtering
- [ ] Update tests/test_alert_analyzer.py
- [ ] Write tests for updated analyze_file() method
- [ ] Write tests for updated get_top_k() method
- [ ] Write tests for get_results() method
- [ ] Write tests for alert_type warning
- [ ] Verify all existing tests still pass

## Prompt 6: Update Command-Line Interface
- [ ] Update src/__main__.py to support new commands
- [ ] Implement process command
- [ ] Implement query command
- [ ] Update main function to parse arguments
- [ ] Create tests/test_cli.py
- [ ] Write tests for process command
- [ ] Write tests for query command
- [ ] Write tests for error handling
- [ ] Ensure backward compatibility with existing interface

## Prompt 7: Update Results Management
- [ ] Update save_results.py to use new components
- [ ] Update ResultsManager class if needed
- [ ] Add new metadata fields if required
- [ ] Create tests for updated save_results.py
- [ ] Create tests for updated list_results.py
- [ ] Verify same functionality and output format

## Prompt 8: Create End-to-End Tests
- [ ] Create test for EventProcessor and QueryEngine workflow
- [ ] Create test for backward compatibility with AlertAnalyzer
- [ ] Create test for command-line interface
- [ ] Create or use sample test file
- [ ] Verify results match expected output

## Prompt 9: Documentation and Final Polishing
- [ ] Update README.md with new architecture
- [ ] Document new components
- [ ] Update usage examples
- [ ] Document new command-line interface
- [ ] Add comprehensive docstrings to new classes and methods
- [ ] Create migration guide for existing API users
- [ ] Run linters and fix issues
- [ ] Check PEP 8 compliance
- [ ] Ensure consistent naming conventions
- [ ] Verify all tests pass
