# Known Limitations

This document outlines known limitations in the current implementation of the Alert Analysis System.

## Alert Type Filtering

### Issue Description

The current implementation does not support filtering by alert type. While the API still accepts an `alert_type` parameter for backward compatibility, it is ignored and a warning is logged.

### Impact

Users cannot filter results to see only entities with specific alert types. All queries return the top k entities based on total unhealthy time across all alert types.

### Workaround

Currently, there is no workaround for this limitation. Users can examine the `alert_types` field in the results to see which alert types affected each entity.

### Future Solution

A proposed solution is outlined in the design document `planning/design/alert_type_filtering.md`. This solution involves:

1. Creating separate indices for each alert type
2. Tracking unhealthy time separately for each alert type
3. Using the appropriate index when filtering by alert type

This would provide accurate unhealthy time calculations when filtering by alert type.
