# Production Engineering Coding Exercise - Alert Analysis

## Problem Summary
The task is to analyze an alert event stream from an internal Alert System. The data comes from a compressed file (`Alert_Event_Data.gz`) containing JSON events that represent when alerts are opened, acknowledged, or closed. The goal is to identify the top 5 "unhealthiest" hosts, defined as those that spent the most total time with one or more open alerts.

## Data Structure
Each alert event contains:
- `event_id`: Unique identifier for the event
- `alert_id`: Unique identifier for the alert
- `timestamp`: When the event occurred
- `state`: Current state of the alert (NEW, ACK, or RSV)
- `type`: Type of alert
- `tags`: Fields specific to the alert type

## Alert States
- `NEW`: Alert is occurring and not acknowledged
- `ACK`: Alert is acknowledged but still occurring
- `RSV`: Alert is resolved and no longer occurring

## Alert Types
The data includes three types of alerts:

1. **Disk Usage Alert**: Volume on host is almost full
   - Tags: dc (data center), host, volume
   
2. **System Service Failed**: Service failed on a host
   - Tags: dc, host, service
   
3. **Time Drift Alert**: Host's clock has drifted from actual time
   - Tags: dc, host, drift (in microseconds)

## Solution Approach
To solve this problem, we need to:

1. **Parse the Data**:
   - Read and decompress the gzipped JSON file
   - Parse each line as a JSON object

2. **Track Alert Lifecycle**:
   - For each host, track when alerts open and close
   - A host is considered "unhealthy" when it has at least one open alert
   - An alert is considered "open" when in either NEW or ACK state
   - An alert is considered "closed" when in RSV state

3. **Calculate Unhealthy Time**:
   - For each host, calculate the total time spent with one or more open alerts
   - Handle overlapping alert periods correctly (don't double-count)

4. **Sort and Report**:
   - Sort hosts by total unhealthy time (descending)
   - Return the top 5 unhealthiest hosts

## Implementation Considerations

### Data Processing
- Use Python's `gzip` module to read the compressed file
- Use `json` module to parse each line
- Consider using pandas for data manipulation if appropriate

### Performance Optimization
- Process the file line by line to minimize memory usage
- Use efficient data structures to track alert states
- Consider using datetime objects for timestamp calculations

### Error Handling
- Handle malformed JSON entries
- Handle missing fields or unexpected values
- Implement proper logging for errors and warnings

### Testing
- Unit tests for individual components
- Integration tests for the full pipeline
- Test with sample data to verify correct calculations

### Output Format
- Present results in a clear, readable format
- Include total unhealthy time for each host
- Consider adding additional metrics if useful (e.g., number of alerts)

## Next Steps
1. Set up project structure
2. Implement data parsing and processing
3. Develop the algorithm to calculate unhealthy time
4. Add tests and error handling
5. Generate the final report
