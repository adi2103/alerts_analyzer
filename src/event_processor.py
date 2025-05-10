"""Event processor for the Alert Analysis System."""

import logging
from datetime import datetime
from typing import Dict

from src.index_manager import IndexManager
from src.models import AlertEvent, AlertState
from src.file_handler import FileHandler
from src.logging_config import configure_logging, log_performance_metrics


class EventProcessor:
    """
    Processes alert events and updates indices.

    The EventProcessor reads alert events from files and updates
    the global indices via the IndexManager.

    Time Complexity:
        - Event processing: O(D) per event where D is the number of dimensions
        - File processing: O(E * D) where E is the number of events

    Space Complexity: O(A) where A is the number of active alerts at any given time
    """

    def __init__(self):
        """Initialize an EventProcessor."""
        # Alert states
        self.alert_states: Dict[str, AlertState] = {}  # alert_id → AlertState

        # Get the index manager
        self.index_manager = IndexManager.get_instance()

        # Configure logging
        configure_logging()
        self.logger = logging.getLogger("event_processor")

    def process_event(self, event: AlertEvent) -> None:
        """
        Process an alert event and update the relevant states and indices.

        Time Complexity: O(D) where D is the number of dimensions
        Space Complexity: O(1) - Uses constant extra space

        Args:
            event: The alert event to process
        """
        # Update alert state
        alert_id = event.alert_id

        # Initialize alert state if needed
        if alert_id not in self.alert_states and event.state != "RSV":
            self.alert_states[alert_id] = AlertState(
                alert_id=alert_id, alert_type=event.type, tags=event.tags
            )

        # Assumption: We skip RSV events for unknown alerts
        if alert_id not in self.alert_states:
            return

        alert_state = self.alert_states[alert_id]
        old_state = alert_state.current_state

        # Update alert state
        alert_state.update_state(event.timestamp, event.state)

        if event.state in ["NEW", "ACK"] and old_state is None:
            # First time seeing this alert - update entity states
            self.index_manager.update_for_new_alert(alert_state, event.timestamp)

        elif event.state == "RSV":
            # Alert is resolved - update entity states and indices
            self.index_manager.update_for_resolved_alert(alert_state, event.timestamp)

            # We can discard the alert state now
            del self.alert_states[alert_id]

    def process_file(self, file_path: str) -> int:
        """
        Process alert events from a file.

        Time Complexity: O(E * D) where:
            - E is the number of events in the file
            - D is the number of dimensions

        Space Complexity: O(A) where A is the number of active alerts at any given time

        Args:
            file_path: Path to the file containing alert events

        Returns:
            Number of events processed

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read
            ValueError: If the file is not a valid file
        """
        # Record start time
        start_time = datetime.now()

        # Create file handler
        file_handler = FileHandler(self.logger)

        # Process events
        events_processed = 0
        try:
            for event in file_handler.read_events(file_path):
                self.process_event(event)
                events_processed += 1
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
            raise

        # Record end time
        end_time = datetime.now()

        # Log performance metrics
        log_performance_metrics(start_time, end_time, events_processed, self.logger)

        return events_processed
