"""Index manager for the Alert Analysis System."""

import logging
from datetime import datetime
from typing import Callable, Dict, Optional

from src.dimension_index import Index
from src.models import AlertState


class IndexManager:
    """
    Manages global indices for the Alert Analysis System.

    The IndexManager maintains indices for different dimensions and provides
    methods to update them when events are processed. It follows the singleton
    pattern to ensure a single global instance is used throughout the application.

    Time Complexity:
        - Dimension registration: O(1) - Constant time dictionary insertion
        - Index lookup: O(1) - Constant time dictionary access

    Space Complexity: O(D * N) where:
        - D is the number of dimensions
        - N is the number of entities across all dimensions
    """

    _instance = None  # Singleton instance

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of IndexManager.

        Returns:
            The singleton IndexManager instance
        """
        if cls._instance is None:
            cls._instance = IndexManager()
        return cls._instance

    def __init__(self):
        """Initialize the IndexManager with standard dimensions."""
        # Registered dimensions for indexing/aggregation
        self.dimensions: Dict[str, Index] = {}  # dimension_name → Index

        # Configure logging
        self.logger = logging.getLogger("index_manager")

        # Register standard dimensions
        self.register_dimension(
            "host", lambda alert_state: alert_state.tags.get("host")
        )
        self.register_dimension(
            "dc", lambda alert_state: alert_state.tags.get("dc")
        )
        self.register_dimension(
            "service", lambda alert_state: alert_state.tags.get("service")
        )
        self.register_dimension(
            "volume", lambda alert_state: alert_state.tags.get("volume")
        )

    def register_dimension(
        self, dimension_name: str, extractor_func: Callable[[AlertState], Optional[str]]
    ) -> None:
        """
        Register a new dimension for indexing and aggregation.

        Time Complexity: O(1) - Constant time dictionary insertion
        Space Complexity: O(1) - Stores a single new Index object

        Args:
            dimension_name: Name of the dimension (e.g., "host", "dc", "service")
            extractor_func: Function that extracts the entity value from an AlertState
        """
        self.dimensions[dimension_name] = Index(dimension_name, extractor_func)
        self.logger.debug(f"Registered dimension: {dimension_name}")

    def update_for_new_alert(
        self, alert_state: AlertState, timestamp: datetime
    ) -> None:
        """
        Update indices when a new alert is created.

        Time Complexity: O(D) where D is the number of dimensions
        Space Complexity: O(1) - Uses constant extra space

        Args:
            alert_state: The alert state
            timestamp: When the alert was created
        """
        # Update each dimension
        for _, dimension_index in self.dimensions.items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue

            # Get or create entity state
            entity_state = dimension_index.get_entity_state(entity_value)

            # Add the alert to the entity
            entity_state.add_alert(alert_state.alert_id, alert_state.type, timestamp)

    def update_for_resolved_alert(
        self, alert_state: AlertState, timestamp: datetime
    ) -> None:
        """
        Update indices when an alert is resolved.

        This method combines the functionality of AlertAnalyzer._update_entity_states_for_resolved_alert
        and AlertAnalyzer._update_indices_for_resolved_alert.

        Time Complexity: O(D * log N) where D is the number of dimensions and N is the number of entities
        Space Complexity: O(1) - Uses constant extra space

        Args:
            alert_state: The alert state
            timestamp: When the alert was resolved
        """
        # Update each dimension
        for dimension_name, dimension_index in self.dimensions.items():
            # Extract entity value for this dimension
            entity_value = dimension_index.extractor_func(alert_state)
            if not entity_value:
                continue

            # Get entity state
            if entity_value in dimension_index.entity_states:
                entity_state = dimension_index.entity_states[entity_value]

                # Remove the alert from the entity
                entity_state.remove_alert(alert_state.alert_id, timestamp)

                # Update position in sorted dict
                old_time = dimension_index.entity_positions.get(entity_value, 0)
                self._update_entity_position(
                    dimension_index,
                    entity_value,
                    old_time,
                    entity_state.total_unhealthy_time,
                )

    def _update_entity_position(
        self,
        dimension_index: Index,
        entity_value: str,
        old_time: float,
        new_time: float,
    ) -> None:
        """
        Update the position of an entity in the sorted index.

        Time Complexity: O(log N) where N is the number of distinct unhealthy times
        Space Complexity: O(1) - Uses constant extra space

        Args:
            dimension_index: The dimension index to update
            entity_value: Value of the entity to update
            old_time: Previous unhealthy time
            new_time: New unhealthy time
        """
        dimension_index.update_entity_position(entity_value, old_time, new_time)

    def get_index(self, dimension_name: str) -> Index:
        """
        Get the index for a specific dimension.

        Time Complexity: O(1) - Constant time dictionary access
        Space Complexity: O(1) - Uses constant extra space

        Args:
            dimension_name: Name of the dimension to get the index for

        Returns:
            Index for the specified dimension

        Raises:
            ValueError: If the dimension is not registered
        """
        if dimension_name not in self.dimensions:
            raise ValueError(f"Dimension {dimension_name} not registered")
        return self.dimensions[dimension_name]
