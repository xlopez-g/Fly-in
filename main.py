#!/usr/bin/env python3
"""Main entry point for the Fly-in drone routing simulation.

This module coordinates map parsing, graph construction, route planning,
and simulation execution while guaranteeing robust exception handling.
"""

import sys

from models import HUB_TYPE, Hub

from parser import parser

from graph import build_graph

from create_drones import create_drones

from print_drones import print_drones

from pydantic import ValidationError


def start_end_hub(hubs: dict[str, Hub]) -> tuple[Hub, Hub]:
    """Locate unique start and end hubs within the network nodes.

    Args:
        hubs: Dictionary mapping hub names to Hub instances.

    Returns:
        A tuple containing (start_hub, end_hub).

    Raises:
        ValueError: If start_hub or end_hub is missing from the network.
    """

    start: Hub | None = None
    goal: Hub | None = None

    for node in hubs.values():
        if node.hub_type == HUB_TYPE.start_hub:
            start = node
        if node.hub_type == HUB_TYPE.end_hub:
            goal = node

    if start is None or goal is None:
        raise ValueError("Start or end hub not found")

    return (start, goal)


def fly_in(entry_file: str) -> None:
    """Execute the complete drone navigation simulation pipeline.

    Args:
        entry_file: Path to the input map configuration file.
    """

    try:
        parsing_data = parser(entry_file)

    except FileNotFoundError:
        print(f"Error: File {entry_file} not found")
        sys.exit(1)
    except OSerror as e:
        print(f"Error while reading {entry_file}", e)
        sys.exit(1)

    nb_drones, hubs, connection_list = parsing_data

    graph = build_graph(hubs, connection_list)

    start, goal = start_end_hub(hubs)

    drone_list = create_drones(nb_drones,
                               graph, hubs, connection_list, start, goal)

    print_drones(drone_list, hubs, connection_list)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("missing file argument")
        print("Usage: make run MAP=<path_to_map>")
        sys.exit(1)

    entry_file = sys.argv[1]
    try:
        fly_in(entry_file)

    except ValidationError as e:
        print("Validation Error", e.errors()[0]["msg"])
        sys.exit(1)

    except ValueError as e:
        print("Error:", e)
        sys.exit(1)

    except exception as e:
        print("Unexpected Error", e)
        sys.exit(1)