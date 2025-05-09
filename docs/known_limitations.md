# Known Limitations

This document outlines known limitations in the current implementation of the Alert Analysis System.

## Alert Type Filtering

### Issue Description

The current implementation has a limitation in how it handles alert type filtering. When filtering by alert type, the system:

1. Ranks entities based on their total unhealthy time across all alert types
2. Includes only entities that have at least one alert of the specified type
3. Does not recalculate unhealthy time to only include time from the specified alert type

### Impact

This approach is problematic because it doesn't accurately represent the "unhealthiest" entities with respect to a specific alert type. For example:

- A host with 10 hours of unhealthy time from "Disk Usage Alert" and 1 minute from "System Service Failed" will rank higher in "System Service Failed" queries than a host with 9 hours of unhealthy time solely from "System Service Failed"
- The unhealthy time reported for entities doesn't reflect the actual time they were unhealthy due to the specified alert type

### Workaround

Currently, there is no workaround for this limitation. Users should be aware that when filtering by alert type, the unhealthy time represents the total time across all alert types, not just the specified type.

### Future Solution

A proposed solution is outlined in the design document `planning/design/alert_type_filtering.md`. This solution involves:

1. Creating separate indices for each alert type
2. Tracking unhealthy time separately for each alert type
3. Using the appropriate index when filtering by alert type

This would provide accurate unhealthy time calculations when filtering by alert type.
