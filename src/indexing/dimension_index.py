"""Dimension indexing for the Alert Analysis System."""

from typing import Dict, Set, Callable, Any, Optional
from sortedcontainers import SortedDict

from src.models import EntityState, AlertState


class Index:
    """
    Maintains an index of entities for a specific dimension.

    An Index provides efficient access to entities ordered by their unhealthy time,
    allowing for quick retrieval of the top k unhealthiest entities.

    Time Complexity:
        - Insertion: O(log N) where N is the number of distinct unhealthy times
        - Top-k query: O(k) where k is the number of results requested
        - Entity lookup: O(1) constant time

    Space Complexity: O(E) where E is the number of entities in this dimension
    """

    def __init__(self,
                 name: str,
                 extractor_func: Callable[[AlertState],
                                          Optional[str]]):
        """
        Initialize an Index.

        Args:
            name: Name of the dimension (e.g., "host", "dc", "service")
            extractor_func: Function that extracts the entity value from an AlertState
        """
        self.name = name
        self.extractor_func = extractor_func

        # Entity states for this dimension
        # entity_value → EntityState
        self.entity_states: Dict[str, EntityState] = {}

        # SortedDict for ordered access
        # Key: -unhealthy_time (negative for reverse order)
        # Value: set of entity_values with that time
        self.ordered_entities = SortedDict()

        # Track current position of each entity in the sorted dict
        # entity_value → unhealthy_time
        self.entity_positions: Dict[str, float] = {}

    def get_entity_state(self, entity_value: str) -> EntityState:
        """
        Get the EntityState for a specific entity value, creating it if it doesn't exist.

        Time Complexity: O(1) - Constant time dictionary access and insertion
        Space Complexity: O(1) - Creates at most one new EntityState

        Args:
            entity_value: Value of the entity (e.g., host ID, data center ID)

        Returns:
            EntityState for the specified entity
        """
        if entity_value not in self.entity_states:
            self.entity_states[entity_value] = EntityState()
            self.entity_positions[entity_value] = 0

        return self.entity_states[entity_value]

    def update_entity_position(
            self,
            entity_value: str,
            old_time: float,
            new_time: float) -> None:
        """
        Update the position of an entity in the ordered index.

        Time Complexity: O(log N) where N is the number of distinct unhealthy times
        Space Complexity: O(1) - Uses constant extra space

        Args:
            entity_value: Value of the entity to update
            old_time: Previous unhealthy time
            new_time: New unhealthy time
        """
        # Remove from old position
        if old_time > 0:
            # Use negative time for reverse ordering (largest first)
            entity_set = self.ordered_entities.get(-old_time, set())
            entity_set.discard(entity_value)
            if not entity_set:
                del self.ordered_entities[-old_time]
            else:
                self.ordered_entities[-old_time] = entity_set

        # Add to new position
        if -new_time not in self.ordered_entities:
            self.ordered_entities[-new_time] = set()
        self.ordered_entities[-new_time].add(entity_value)
        self.entity_positions[entity_value] = new_time

    def get_top_k(self, k: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Get the top k entities by unhealthy time.

        Time Complexity: O(k) - Linear in the number of results requested
        Space Complexity: O(k) - Stores k result entities

        Args:
            k: Number of entities to return

        Returns:
            Dictionary mapping entity values to their details
        """
        results = {}
        count = 0

        for neg_time, entity_values in self.ordered_entities.items():
            for entity_value in entity_values:
                entity_state = self.entity_states[entity_value]

                results[entity_value] = {
                    f"{self.name}_id": entity_value,
                    "total_unhealthy_time": -neg_time,  # Convert back to positive
                    "alert_types": dict(entity_state.alert_type_counts)
                }

                count += 1
                if count >= k:
                    return results

        return results

    def __repr__(self) -> str:
        """Return a string representation of the Index."""
        return f"Index(name={self.name}, entities={len(self.entity_states)})"
