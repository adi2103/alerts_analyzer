"""Data models for the Alert Analysis System."""

import json
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from dateutil import parser


class AlertEvent:
    """
    Represents an alert event from the alert system.

    An alert event contains information about a specific alert at a point in time,
    including its state (NEW, ACK, or RSV), type, and associated metadata.
    """

    def __init__(
        self,
        event_id: str,
        alert_id: str,
        timestamp: datetime,
        state: str,
        alert_type: str,
        tags: Dict[str, Any],
    ):
        """
        Initialize an AlertEvent.

        Args:
            event_id: Unique identifier for the event
            alert_id: Unique identifier for the alert
            timestamp: When the event occurred
            state: Current state of the alert (NEW, ACK, or RSV)
            alert_type: Type of alert
            tags: Fields specific to the alert type
        """
        self.event_id = event_id
        self.alert_id = alert_id
        self.timestamp = timestamp
        self.state = state
        self.type = alert_type
        self.tags = tags

    @classmethod
    def from_json(cls, json_data: Union[str, Dict]) -> "AlertEvent":
        """
        Create an AlertEvent from JSON data.

        Args:
            json_data: JSON string or dictionary containing event data

        Returns:
            An AlertEvent instance

        Raises:
            ValueError: If the JSON data is missing required fields or has invalid values
            json.JSONDecodeError: If the JSON string is malformed
        """
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data

        # Validate required fields
        required_fields = ["event_id", "alert_id", "timestamp", "state", "type", "tags"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate state
        if data["state"] not in ["NEW", "ACK", "RSV"]:
            raise ValueError(f"Invalid state: {data['state']}")

        # Parse timestamp
        try:
            timestamp = parser.parse(data["timestamp"])
        except (ValueError, TypeError):
            raise ValueError(f"Invalid timestamp: {data['timestamp']}")

        return cls(
            event_id=data["event_id"],
            alert_id=data["alert_id"],
            timestamp=timestamp,
            state=data["state"],
            alert_type=data["type"],
            tags=data["tags"],
        )

    def __repr__(self) -> str:
        """Return a string representation of the AlertEvent."""
        return (
            f"AlertEvent(event_id={
                self.event_id}, alert_id={
                self.alert_id}, "
            f"timestamp={
                self.timestamp}, state={
                    self.state}, type={
                        self.type})"
        )


class AlertState:
    """
    Tracks the state of an alert over time.

    An AlertState maintains the current state of an alert and its history,
    including when it was first opened and when it was resolved.
    """

    def __init__(self, alert_id: str, alert_type: str, tags: Dict[str, Any]):
        """
        Initialize an AlertState.

        Args:
            alert_id: Unique identifier for the alert
            alert_type: Type of alert
            tags: Fields specific to the alert type
        """
        self.alert_id = alert_id
        self.type = alert_type
        self.tags = tags
        self.current_state: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.state_history: List[Tuple[datetime, str]] = []

    def update_state(self, timestamp: datetime, state: str) -> None:
        """
        Update the alert state with a new event.

        Args:
            timestamp: When the state change occurred
            state: New state of the alert (NEW, ACK, or RSV)
        """
        # Record the state change in history
        self.state_history.append((timestamp, state))

        # Update current state
        self.current_state = state

        # Update start/end times
        if state in ["NEW", "ACK"] and self.start_time is None:
            self.start_time = timestamp
        elif state == "RSV":
            self.end_time = timestamp

    def is_active(self) -> bool:
        """
        Check if the alert is currently active (not resolved).

        Returns:
            True if the alert is active, False otherwise
        """
        return self.current_state not in ["RSV"]

    def get_duration(self) -> Optional[float]:
        """
        Calculate the duration of the alert in seconds.

        Returns:
            Duration in seconds if the alert has both start and end times,
            None otherwise
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def __repr__(self) -> str:
        """Return a string representation of the AlertState."""
        return (
            f"AlertState(alert_id={self.alert_id}, type={self.type}, "
            f"current_state={self.current_state})"
        )


class EntityState:
    """
    Tracks the health state of an entity over time.

    An EntityState maintains information about the total time an entity spent in an
    unhealthy state, the currently active alerts, and historical data for analysis.
    """

    def __init__(self):
        """Initialize an EntityState."""
        self.total_unhealthy_time: float = 0
        self.current_alerts: Set[str] = set()  # Set of active alert_ids
        # Timestamp when entity became unhealthy
        self.unhealthy_start: Optional[datetime] = None

        # Time series data for temporal analysis
        # List of (start_time, end_time) tuples
        self.unhealthy_periods: List[Tuple[datetime, datetime]] = []

        # For reporting
        self.alert_type_counts: Dict[str, int] = defaultdict(int)

    def add_alert(self, alert_id: str, alert_type: str, timestamp: datetime) -> None:
        """
        Add an active alert to the entity.

        Args:
            alert_id: Unique identifier for the alert
            alert_type: Type of alert
            timestamp: When the alert was added
        """
        # Add to current alerts
        self.current_alerts.add(alert_id)

        # Update alert type counts
        self.alert_type_counts[alert_type] += 1

        # If this is the first alert, mark the start of unhealthy period
        if len(self.current_alerts) == 1:
            self.unhealthy_start = timestamp

    def remove_alert(self, alert_id: str, timestamp: datetime) -> None:
        """
        Remove an active alert from the entity.

        Args:
            alert_id: Unique identifier for the alert
            timestamp: When the alert was removed
        """
        # Remove from current alerts
        if alert_id in self.current_alerts:
            self.current_alerts.remove(alert_id)

        # If no more alerts, calculate unhealthy time and reset
        if not self.current_alerts and self.unhealthy_start:
            # Calculate duration of this unhealthy period
            duration = (timestamp - self.unhealthy_start).total_seconds()
            self.total_unhealthy_time += duration

            # Record the unhealthy period
            self.unhealthy_periods.append((self.unhealthy_start, timestamp))

            # Reset unhealthy start
            self.unhealthy_start = None

    def is_unhealthy(self) -> bool:
        """
        Check if the entity is currently unhealthy (has active alerts).

        Returns:
            True if the entity is unhealthy, False otherwise
        """
        return len(self.current_alerts) > 0

    def calculate_unhealthy_time_in_range(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate unhealthy time within a specific time range.

        Args:
            start_time: Start of the time range (None for no lower bound)
            end_time: End of the time range (None for no upper bound)

        Returns:
            Total unhealthy time in seconds within the specified range
        """
        unhealthy_time = 0

        for period_start, period_end in self.unhealthy_periods:
            # Skip periods outside the range
            if (start_time and period_end < start_time) or (
                end_time and period_start > end_time
            ):
                continue

            # Adjust period to the specified range
            overlap_start = (
                max(period_start, start_time) if start_time else period_start
            )
            overlap_end = min(period_end, end_time) if end_time else period_end

            # Add the overlap duration
            unhealthy_time += (overlap_end - overlap_start).total_seconds()

        return unhealthy_time

    def __repr__(self) -> str:
        """Return a string representation of the EntityState."""
        return (
            f"EntityState(total_unhealthy_time={
                self.total_unhealthy_time}, "
            f"current_alerts={
                len(
                    self.current_alerts)}, "
            f"is_unhealthy={
                    self.is_unhealthy()})"
        )
