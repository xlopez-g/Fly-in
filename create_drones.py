#!/usr/bin/env python3

from models import Hub, Drone, Reservation_Table, Connection

from dijkstra import dijkstra


def create_Drones(nb_drones: int,
                  graph: dict[Hub, dict[Hub, dict[str, int]]],
                  hubs: dict[str, "Hub"],
                  connection_list: list["Connection"],
                  start: Hub,
                  goal: Hub
                  ) -> list[Drone]:

    hub_load: dict[tuple[Hub, int], int] = {}
    c_occupancy: dict[tuple[Hub, Hub, int], int] = {}

    reservation_table = Reservation_Table(hub_load=hub_load,
                                          conn_load=c_occupancy)

    drone_list: list[Drone] = []

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

    return drone_list
