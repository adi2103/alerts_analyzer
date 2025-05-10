"""Query engine for the Alert Analysis System."""

import logging
from typing import Any, Dict, List

from src.index_manager import IndexManager
from src.logging_config import configure_logging


class QueryEngine:
    """
    Queries indices for unhealthy entities.

    The QueryEngine provides methods to query the global indices
    for the top k unhealthiest entities.

    Time Complexity:
        - Top-k query: O(k) - Linear in the number of results requested

    Space Complexity: O(k) - Stores k result entities
    """

    def __init__(self):
        """Initialize a QueryEngine."""
        # Get the index manager
        self.index_manager = IndexManager.get_instance()

        # Configure logging
        configure_logging()
        self.logger = logging.getLogger("query_engine")

    def get_top_k(self, dimension_name: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get top k entities by unhealthy time for a specific dimension.

        Time Complexity: O(k) - Linear in the number of results requested
        Space Complexity: O(k) - Stores k result entities

        Args:
            dimension_name: Name of the dimension to query
            k: Number of entities to return

        Returns:
            List of dictionaries containing entity details, sorted by unhealthy time

        Raises:
            ValueError: If the dimension is not registered
        """
        try:
            # Get the index for the specified dimension
            index = self.index_manager.get_index(dimension_name)

            # Get top k entities
            results = []
            count = 0
            processed_entities = set()  # Track entities we've already processed

            for neg_time, entity_values in index.ordered_entities.items():
                for entity_value in entity_values:
                    # Skip entities we've already processed (avoid duplicates)
                    if entity_value in processed_entities:
                        continue

                    entity_state = index.entity_states[entity_value]

                    # Add to results and mark as processed
                    results.append(
                        {
                            f"{dimension_name}_id": entity_value,
                            "total_unhealthy_time": -neg_time,  # Convert back to positive
                            "alert_types": dict(entity_state.alert_type_counts),
                        }
                    )
                    processed_entities.add(entity_value)

                    count += 1
                    if count >= k:
                        return results

            return results
        except ValueError as e:
            self.logger.error(f"Error querying dimension {dimension_name}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_top_k: {e}")
            raise
