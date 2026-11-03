#!/usr/bin/env python3

from models import Hub, Connection, Reservation_Table


def dijkstra(graph: dict[Hub, dict[Hub, dict[str, int]]],
             hubs: dict[str, "Hub"],
             connection_list: list["Connection"],
             reservation_table: Reservation_Table,
             start: Hub,
             goal: Hub) -> tuple[list[tuple[Hub, int]], int | float]:

    if goal == start:
        return ([(start, 0)], 0)

    distances: dict[tuple[Hub, int], int | float] = {}
    previous = {}
    unvisited = set()

    from_node = (start, 0)

    distances[(start, 0)] = 0
    unvisited.add((start, 0))

    final_turn = None

    while (unvisited):
        turn = from_node[1]
        unvisited.remove(from_node)

        if from_node[0] == goal:
            final_turn = from_node[1]
            break

        options_to_check = []
        options_to_check.append(from_node[0])
        for node in list(graph[from_node[0]].keys()):
            options_to_check.append(node)

        for next_node in options_to_check:
            if next_node == from_node[0]:
                cost_node = 1
                max_drones = from_node[0].max_drones

                if not (reservation_table.is_hub_available(from_node[0],
                                                           turn + cost_node,
                                                           max_drones)):
                    continue

            else:

                cost_node = graph[from_node[0]][next_node]["cost"]
                max_drones = next_node.max_drones

                if not (reservation_table.is_hub_available(next_node,
                                                           turn + cost_node,
                                                           max_drones)):
                    continue

                max_link_capacity = graph[from_node[0]][next_node]["capacity"]

                conec_avai = reservation_table.is_connection_available

                if not (conec_avai(from_node[0],
                                   next_node,
                                   turn + cost_node,
                                   max_link_capacity)):
                    continue

                restricted_True = (conec_avai(from_node[0],
                                              next_node,
                                              turn + cost_node - 1,
                                              max_link_capacity))

                if (cost_node == 2 and not restricted_True):
                    continue

            distance_next_node = distances.get((next_node,
                                                turn + cost_node),
                                               float("inf"))

            new_posible_distance = distances[from_node] + cost_node

            if (distance_next_node > new_posible_distance):
                distances[(next_node, turn + cost_node)] = new_posible_distance
                previous[(next_node, turn + cost_node)] = from_node
                unvisited.add((next_node, turn + cost_node))
        min_cost = float("inf")
        current_state = None

        min_tuple_list = list(distances.keys())

        for (node, turn_i) in min_tuple_list:
            possible_distance = distances[(node, turn_i)]
            if ((node, turn_i) in unvisited and possible_distance < min_cost):
                min_cost = distances[(node, turn_i)]
                current_state = (node, turn_i)

        if current_state is None or min_cost == float("inf"):
            break

        from_node = current_state

    if final_turn is None:
        return ([(start, 0)], float("inf"))

    reverse_path = [(goal, final_turn)]
    point = (goal, final_turn)

    while ((start, 0) not in reverse_path):
        next_point = previous[point]
        reverse_path.append(next_point)
        point = next_point

    path = reverse_path[:: -1]

    return (path, distances[(goal, final_turn)])
