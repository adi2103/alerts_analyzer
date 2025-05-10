"""Command-line interface for the Alert Analysis System."""

import argparse
import sys
import json
from typing import List, Dict, Any

from src.alert_analyzer import AlertAnalyzer
from src.processors.event_processor import EventProcessor
from src.query.query_engine import QueryEngine
from src.utils.logging_config import configure_logging


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Alert Analysis System")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create parser for the "process" command
    process_parser = subparsers.add_parser("process", help="Process events from a file")
    process_parser.add_argument(
        "file_path",
        help="Path to the gzipped JSON file containing alert events"
    )
    
    # Create parser for the "query" command
    query_parser = subparsers.add_parser("query", help="Query top k unhealthiest entities")
    query_parser.add_argument(
        "dimension",
        help="Dimension to analyze (e.g., host, dc, service, volume)"
    )
    query_parser.add_argument(
        "--top", "-k",
        type=int,
        default=5,
        help="Number of entities to return (default: 5)"
    )
    query_parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    query_parser.add_argument(
        "--format", "-f",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Create parser for the legacy mode (backward compatibility)
    legacy_parser = subparsers.add_parser("legacy", help="Legacy mode (backward compatibility)")
    legacy_parser.add_argument(
        "file_path",
        help="Path to the gzipped JSON file containing alert events"
    )
    legacy_parser.add_argument(
        "--dimension", "-d",
        default="host",
        help="Dimension to analyze (default: host)"
    )
    legacy_parser.add_argument(
        "--top", "-k",
        type=int,
        default=5,
        help="Number of entities to return (default: 5)"
    )
    legacy_parser.add_argument(
        "--alert-type", "-t",
        help="Filter by alert type"
    )
    legacy_parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    legacy_parser.add_argument(
        "--format", "-f",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )
    
    # For backward compatibility, if no command is specified but a file path is provided,
    # assume legacy mode
    args, unknown = parser.parse_known_args()
    if args.command is None and unknown:
        # Check if the first unknown arg looks like a file path
        if not unknown[0].startswith('-'):
            args = parser.parse_args(['legacy'] + unknown)
    
    return args


def format_results(results: List[Dict[str, Any]], format_type: str) -> str:
    """
    Format results for output.

    Args:
        results: List of dictionaries containing entity details
        format_type: Output format (json or text)

    Returns:
        Formatted results as a string
    """
    if format_type == "json":
        return json.dumps(results, indent=2)

    # Text format
    output = []
    output.append("Top Unhealthy Entities:")
    output.append("======================")

    for i, entity in enumerate(results, 1):
        # Get the entity ID (could be host_id, dc_id, etc.)
        entity_id_key = next(
            (k for k in entity.keys() if k.endswith("_id")), None)
        entity_id = entity.get(entity_id_key, "Unknown")

        output.append(f"{i}. {entity_id}")
        output.append(
            f"   Total Unhealthy Time: {
                entity['total_unhealthy_time']} seconds")

        if entity['alert_types']:
            output.append("   Alert Types:")
            for alert_type, count in entity['alert_types'].items():
                output.append(f"     - {alert_type}: {count}")

        output.append("")

    return "\n".join(output)


def main() -> None:
    """Main entry point for the command-line interface."""
    # Configure logging
    configure_logging()

    # Parse arguments
    args = parse_args()

    try:
        if args.command == "process":
            # Process command
            processor = EventProcessor()
            events_processed = processor.process_file(args.file_path)
            print(f"Processed {events_processed} events from {args.file_path}")
            
        elif args.command == "query":
            # Query command
            query_engine = QueryEngine()
            results = query_engine.get_top_k(args.dimension, args.top)
            
            # Format results
            output = format_results(results, args.format)
            
            # Write output
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
                
        else:  # Legacy mode or no command specified
            # Create analyzer (backward compatibility)
            analyzer = AlertAnalyzer()

            # Analyze file
            results = analyzer.analyze_file(
                args.file_path,
                args.dimension,
                args.top,
                getattr(args, 'alert_type', None)
            )

            # Format results
            output = format_results(results, args.format)

            # Write output
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
