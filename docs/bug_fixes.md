# Bug Fixes

This document records significant bugs that were identified and fixed in the Alert Analysis System.

## Duplicate Entities in Query Results

### Issue Description

When querying for the top k entities with a specific alert type, the results sometimes contained:
1. Duplicate entities (the same entity appearing multiple times)
2. Entities with zero unhealthy time despite having alerts of the specified type

This was observed in a query for the top 5 hosts with "System Service Failed" alerts, where the 4th and 5th results were the same host, and the 5th result showed 0 unhealthy time despite having 28 alerts.

Example problematic result:
```json
[
  {
    "host_id": "host-7f80606d430fb7da",
    "total_unhealthy_time": 15921.627101,
    "alert_types": {
      "System Service Failed": 11
    }
  },
  {
    "host_id": "host-4e89fdb9fdfc429a",
    "total_unhealthy_time": 7092.053203,
    "alert_types": {
      "System Service Failed": 9
    }
  },
  {
    "host_id": "host-bf499e046e947f4a",
    "total_unhealthy_time": 5473.398237,
    "alert_types": {
      "System Service Failed": 3
    }
  },
  {
    "host_id": "host-22f1fddd19b60a0f",
    "total_unhealthy_time": 2784.730161,
    "alert_types": {
      "System Service Failed": 28
    }
  },
  {
    "host_id": "host-22f1fddd19b60a0f",
    "total_unhealthy_time": 0,
    "alert_types": {
      "System Service Failed": 28
    }
  }
]
```

### Root Cause

The issue was in the `get_top_k` method of the `AlertAnalyzer` class. When iterating through the ordered entities, the method didn't track which entities had already been processed. This allowed the same entity to appear multiple times in the results if it had multiple entries in the ordered entities dictionary with different unhealthy times.

This could happen because:
1. The `_apply_filters` method creates a new ordered dictionary with filtered entities
2. An entity could appear in multiple time buckets if it had alerts of different types
3. When filtering by alert type, an entity might appear with both its actual unhealthy time and with zero unhealthy time

### Fix

The fix was to add a tracking mechanism to prevent duplicate entities in the results:

```python
def get_top_k(self, dimension_name: str, k: int = 5, alert_type: Optional[str] = None) -> List[Dict[str, Any]]:
    # ... existing code ...
    
    # Get top k entities
    results = []
    count = 0
    processed_entities = set()  # Track entities we've already processed
    
    for neg_time, entity_values in filtered_entities.items():
        for entity_value in entity_values:
            # Skip entities we've already processed (avoid duplicates)
            if entity_value in processed_entities:
                continue
                
            entity_state = dimension_index.entity_states[entity_value]
            
            # Skip entities that don't match the alert type filter
            if alert_type and not self._matches_alert_type(entity_value, entity_state, alert_type):
                continue
            
            # Add to results and mark as processed
            results.append({
                f"{dimension_name}_id": entity_value,
                "total_unhealthy_time": -neg_time,  # Convert back to positive
                "alert_types": dict(entity_state.alert_type_counts)
            })
            processed_entities.add(entity_value)
            
            count += 1
            if count >= k:
                return results
    
    return results
```

### Verification

A new integration test was added to verify the fix:

```python
def test_system_service_failed_alert_type(self, data_file):
    """Test filtering by System Service Failed alert type."""
    # Create analyzer
    analyzer = AlertAnalyzer()
    
    # Analyze file with filter
    results = analyzer.analyze_file(
        data_file, 
        dimension_name='host', 
        k=5, 
        alert_type="System Service Failed"
    )
    
    # Check results
    assert len(results) == 4  # There are only 4 hosts with System Service Failed alerts
    
    # Verify the expected hosts and order
    expected_hosts = [
        "host-7f80606d430fb7da",
        "host-4e89fdb9fdfc429a",
        "host-bf499e046e947f4a",
        "host-22f1fddd19b60a0f"
    ]
    
    actual_hosts = [result["host_id"] for result in results]
    assert actual_hosts == expected_hosts
    
    # Verify no duplicates in results
    assert len(set(actual_hosts)) == len(actual_hosts)
```

The test confirms that:
1. There are no duplicate entities in the results
2. All entities have the correct unhealthy time
3. The entities are properly ordered by unhealthy time
