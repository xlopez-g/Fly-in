#!/usr/bin/env python3

import sys

from models import HUB_TYPE, Hub, Drone, Reservation_Table

from parser import parser

from graph import build_graph

from dijkstra import dijkstra

from print_drones import print_drones

from pydantic import ValidationError


def program(entry_file: str) -> None:

    try:
        parsing = parser(entry_file)
    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(1)

    nb_drones = parsing[0]

    hubs = parsing[1]

    connection_list = parsing[2]

    graph = build_graph(hubs, connection_list)

    for node in hubs:
        if hubs[node].hub_type == HUB_TYPE.start_hub:
            start = hubs[node]
        if hubs[node].hub_type == HUB_TYPE.end_hub:
            goal = hubs[node]

    hub_load: dict[tuple[Hub, int], int] = {}
    c_occupancy: dict[tuple[Hub, Hub, int], int] = {}
    reservation_table = Reservation_Table(hub_load=hub_load,
                                          conn_load=c_occupancy)

    drone_list = []

    for drone_number in range(nb_drones):
        path, distance = dijkstra(graph, hubs, connection_list,
                                  reservation_table, start, goal)

        start_hub, start_turn = path[0]
        reservation_table.reserve_hub(start_hub, start_turn)

        drone = Drone(id=(f"D{drone_number + 1}"), path=path, path_index=0)

        for step in range(len(path) - 1):
            this_hub = path[step][0]
            this_turn = path[step][1]
            next_hub = path[step + 1][0]
            next_turn = path[step + 1][1]

            reservation_table.reserve_hub(next_hub, next_turn)

            if this_hub != next_hub:
                for turn in range(this_turn + 1, next_turn + 1):
                    reservation_table.reserve_connection(
                        this_hub, next_hub, turn)
        drone_list.append(drone)

    print_drones(drone_list, hubs, connection_list)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        raise ValueError("missing file argument")

    entry_file = sys.argv[1]
    try:
        program(entry_file)

    except ValidationError as e:
        print(e.errors()[0]["msg"])
        sys.exit(1)

    except ValueError as e:
        print("Error:", e)
        sys.exit(1)
