#!/usr/bin/env python3

import sys

from models import HUB_TYPE, Hub, Drone, Reservation_Table, Connection

from parser import parser

from graph import build_graph

from create_drones import create_Drones

from print_drones import print_drones

from pydantic import ValidationError


def start_end_hub(hubs: dict[str, Hub]) -> tuple[Hub, Hub]:

    start = None
    goal = None

    for node in hubs:
        if hubs[node].hub_type == HUB_TYPE.start_hub:
            start = hubs[node]
        if hubs[node].hub_type == HUB_TYPE.end_hub:
            goal = hubs[node]

    if start is None or goal is None:
        raise ValueError("Start or end hub not found")

    return (start, goal)


def fly_in(entry_file: str) -> None:

    try:
        parsing_data = parser(entry_file)

    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(1)

    nb_drones, hubs, connection_list = parsing_data

    graph = build_graph(hubs, connection_list)

    start, goal = start_end_hub(hubs)

    drone_list = create_Drones(nb_drones,
                               graph, hubs, connection_list, start, goal)

    print_drones(drone_list, hubs, connection_list)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        raise ValueError("missing file argument")

    entry_file = sys.argv[1]
    try:
        fly_in(entry_file)

    except ValidationError as e:
        print(e.errors()[0]["msg"])
        sys.exit(1)

    except ValueError as e:
        print("Error:", e)
        sys.exit(1)
