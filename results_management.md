# Results Management

The Alert Analysis System includes a comprehensive results management system that allows you to save, load, and list analysis results with their associated query metadata.

## Overview

The results management system provides the following capabilities:

1. **Save analysis results** with query metadata (timestamp, data file, parameters)
2. **Load previously saved results** for further analysis or comparison
3. **List all saved results** with their query parameters

## Results Format

Results are saved in a structured JSON format that includes both query metadata and the actual results:

```json
{
  "query": {
    "timestamp": "2025-05-09T07:04:43.762144",
    "parameters": {
      "dimension": "host",
      "top_k": 3,
      "alert_type": null
    }
  },
  "results": [
    {
      "host_id": "host-89a9a342729c4e5b",
      "total_unhealthy_time": 145521.49419099998,
      "alert_types": {
        "Disk Usage Alert": 9
      }
    },
    ...
  ]
}
```

## Command-line Interface

### Saving Results

```bash
python save_results.py <file_path> [options]
```

Options:
- `--dimension`, `-d`: Dimension to analyze (default: host)
- `--top`, `-k`: Number of entities to return (default: 5)
- `--alert-type`, `-t`: Filter by alert type

Example:
```bash
python save_results.py data/Alert_Event_Data.gz --dimension dc --top 3
```

Output:
```
Results saved to results/query_results_20250509_070443.json

Top 3 Unhealthiest DCs:
========================================
1. dc-2cda36e6665669fd: 65619.42 seconds
   Alert Types:
     - Time Drift Alert: 1
     - Disk Usage Alert: 4

2. dc-ed1f57a0af343b9e: 63172.24 seconds
   Alert Types:
     - Disk Usage Alert: 13

3. dc-242b06fc7dbbcaf5: 47317.33 seconds
   Alert Types:
     - Disk Usage Alert: 18
     - Time Drift Alert: 2
```

### Listing Saved Results

```bash
python list_results.py
```

Output:
```
Found 3 saved results:
================================================================================
1. query_results_20250509_070443.json
   Timestamp: 2025-05-09T07:04:43.762144
   Data File: data/Alert_Event_Data.gz
   Query: Top 3 hosts
   Result Count: 3
--------------------------------------------------------------------------------
2. query_results_20250509_070215.json
   Timestamp: 2025-05-09T07:02:15.283295
   Data File: data/Alert_Event_Data.gz
   Query: Top 3 dcs
   Result Count: 3
--------------------------------------------------------------------------------
3. query_results_20250509_070141.json
   Timestamp: 2025-05-09T07:01:41.470046
   Data File: data/Alert_Event_Data.gz
   Query: Top 5 hosts
   Result Count: 5
--------------------------------------------------------------------------------
```

## Python API

### ResultsManager Class

The `ResultsManager` class provides the core functionality for managing results:

```python
from src.utils.results_manager import ResultsManager

# Create results manager
results_manager = ResultsManager()

# Save results
filename, saved_results = results_manager.save_results(
    results,                  # List of result dictionaries
    "data/Alert_Event_Data.gz",  # Data file path
    "host",                   # Dimension name
    5,                        # Number of entities
    "Disk Usage Alert"        # Optional alert type filter
)

# List all saved results
all_results = results_manager.list_results()
for result in all_results:
    print(f"{result['filename']}: {result['dimension']} - {result['top_k']} results")

# Load a specific result
loaded_result = results_manager.load_results(filename)
```

### Integration with AlertAnalyzer

The results management system integrates seamlessly with the `AlertAnalyzer` class:

```python
from src.alert_analyzer import AlertAnalyzer
from src.utils.results_manager import ResultsManager

# Create analyzer and results manager
analyzer = AlertAnalyzer()
results_manager = ResultsManager()

# Analyze file
results = analyzer.analyze_file(
    "data/Alert_Event_Data.gz",
    dimension_name="host",
    k=5,
    alert_type="Disk Usage Alert"
)

# Save results with metadata
filename, saved_results = results_manager.save_results(
    results,
    "data/Alert_Event_Data.gz",
    "host",
    5,
    "Disk Usage Alert"
)
```

## Benefits

The results management system provides several benefits:

1. **Reproducibility**: Each saved result includes the exact query parameters used
2. **Traceability**: Timestamps and data file information help track when and on what data the analysis was performed
3. **Comparison**: Multiple analyses can be saved and compared
4. **Persistence**: Results can be saved and loaded for later use
5. **Documentation**: The saved metadata serves as documentation for the analysis
