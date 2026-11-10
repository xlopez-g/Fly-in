#!/usr/bin/env python3
"""Time-expanded Dijkstra pathfinding algorithm for Fly-in.

Calculates optimal time-indexed paths for drones over a dynamic network graph,
accounting for zone costs, priority weightings, waiting actions, and capacity
constraints across future turns.
"""

from models import Hub, Connection, Zone_class, Reservation_Table


def dijkstra(graph: dict[Hub, dict[Hub, dict[str, int]]],
             hubs: dict[str, Hub],
             connection_list: list[Connection],
             reservation_table: Reservation_Table,
             start: Hub,
             goal: Hub) -> tuple[list[tuple[Hub, int]], int | float]:
    """Find the shortest conflict-free path from start to goal over time.

    Args:
        graph: Adjacency dictionary mapping Hub connections, costs,
               and link caps.
        hubs: Map of hub name to Hub instances.
        connection_list: List of parsed Connection objects.
        reservation_table: Hub occupancy and connection capacity tracker.
        start: Starting Hub object.
        goal: Target Hub object.

    Returns:
        A tuple containing (list_of_hub_turn_tuples, total_path_cost).
    """

    distances: dict[tuple[Hub, int], int | float] = {}
    previous: dict[tuple[Hub, int], tuple[Hub, int]] = {}
    unvisited: set[tuple[Hub, int]] = set()

    from_node = (start, 0)

    distances[from_node] = 0
    unvisited.add(from_node)

    if goal == start:
        return ([from_node], 0)

    final_turn = None

    while unvisited:

        unvisited.remove(from_node)
        turn = from_node[1]
        from_hub = from_node[0]

        if from_hub == goal:
            final_turn = turn
            break

        options_to_check = []
        options_to_check.append(from_hub)
        for node in list(graph[from_hub].keys()):
            options_to_check.append(node)

        for next_node in options_to_check:

            if turn > 100:
                continue

            if next_node == from_hub:
                cost_node = 0.999
                max_drones = from_hub.max_drones

                total_cost = turn + round(cost_node)
                if not (reservation_table.is_hub_available(from_hub,
                                                           total_cost,
                                                           max_drones)):
                    continue

            else:

                if next_node.zone == Zone_class.priority:
                    cost_node = 0.99
                else:
                    cost_node = graph[from_hub][next_node]["cost"]

                max_drones = next_node.max_drones
                total_cost = turn + round(cost_node)

                if not (reservation_table.is_hub_available(next_node,
                                                           total_cost,
                                                           max_drones)):
                    continue

                max_link_capacity = graph[from_hub][next_node]["capacity"]

                conec_avai = reservation_table.is_connection_available

                if not (conec_avai(from_hub,
                                   next_node,
                                   turn + round(cost_node),
                                   max_link_capacity)):
                    continue

                restricted_True = (conec_avai(from_hub,
                                              next_node,
                                              turn + round(cost_node) - 1,
                                              max_link_capacity))

                if (cost_node == 2 and not restricted_True):
                    continue

            distance_next_node = distances.get((next_node,
                                                round(turn + cost_node)),
                                               float("inf"))

            new_posible_distance = float(distances[from_node]) + cost_node

            if (distance_next_node > new_posible_distance):
                cost_node = round(cost_node)
                distances[(next_node, turn + cost_node)] = new_posible_distance
                previous[(next_node, turn + cost_node)] = from_node
                unvisited.add((next_node, turn + cost_node))

        min_cost = float("inf")
        current_state = None

        for (node, turn_i) in unvisited:
            possible_distance = distances.get((node, turn_i), float("inf"))
            if possible_distance < min_cost:
                min_cost = possible_distance
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

    path = reverse_path[::-1]

    return (path, distances[(goal, final_turn)])
