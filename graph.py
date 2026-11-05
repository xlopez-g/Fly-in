#!/usr/bin/env python3
"""Graph construction module for the Fly-in drone routing simulation.

Converts hubs and connection lists into an adjacency map representation,
taking into account zone movement costs and connection link capacities.
"""

from models import Zone_class, Hub, Connection

GraphType = dict[Hub, dict[Hub, dict[str, int]]]


def get_zone_cost(zone: Zone_class) -> None | int:
    """Calculate turn cost associated with entering a specific zone type.

    Args:
        zone: Zone classification of the destination hub.

    Returns:
        Integer cost in simulation turns (1 for normal/priority, 2 for restricted),
        or None if the zone is blocked (inaccessible).
    """

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




def build_graph(hubs: dict[str, Hub],
                connection_list: list[Connection]) -> GraphType:
    """Build a directed adjacency graph from network hubs and connections.

    Assigns directional movement costs based on the target hub's zone type
    and incorporates connection link capacities.

    Args:
        hubs: Dictionary of hub name to Hub model instances.
        connection_list: List of parsed Connection instances.

    Returns:
        A nested dictionary mapping origin Hub -> destination Hub -> metadata dict
        containing 'cost' and 'capacity'.
    """

    graph: GraphType = {}

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
