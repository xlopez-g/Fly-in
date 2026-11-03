#!/usr/bin/env python3

from models import Zone_class, Hub, Connection


def get_zone_cost(zone: Zone_class) -> None | int:
    cost = None
    if zone == Zone_class.normal:
        cost = 1
    elif zone == Zone_class.blocked:
        cost = None
    elif zone == Zone_class.restricted:
        cost = 2
    elif zone == Zone_class.priority:
        cost = 1
    return (cost)


graph_form = dict[Hub, dict[Hub, dict[str, int]]]


def build_graph(hubs: dict[str, "Hub"],
                connection_list: list["Connection"]) -> graph_form:

    graph: dict[Hub, dict[Hub, dict[str, int]]] = {}

    for hub in hubs.values():
        graph[hub] = {}

    for connection in connection_list:
        hub_a = connection.hub_a
        hub_in = hubs[hub_a]
        hub_b = connection.hub_b
        hub_to = hubs[hub_b]
        capacity = connection.max_link_capacity

        cost_a_to_b = get_zone_cost(hub_to.zone)
        cost_b_to_a = get_zone_cost(hub_in.zone)

        if cost_a_to_b is not None:
            graph[hub_in][hub_to] = {
                "cost": cost_a_to_b,
                "capacity": capacity
            }

        if cost_b_to_a is not None:
            graph[hub_to][hub_in] = {
                "cost": cost_b_to_a,
                "capacity": capacity
            }
    return (graph)
