#!/usr/bin/env python3

from enum import Enum

import sys

class Zone_class(Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


def parser(read_file: str):

    nb_drones = 0
    hubs = {}
    connection_list = []

    with open(read_file, "r") as entry_file:

        for line in entry_file:
            line = line.strip()
            
            if not line or line.startswith("#"):
                continue

            if line.startswith("nb_drones:"):
                nb_drones = int(line.split(":")[1].strip())

            elif line.startswith(("start_hub:", "hub:", "end_hub:")):
                hub_type, hub_data = line.split(":", 1)
                parts = hub_data.strip().split(None, 3)

                name = parts[0]
                x = int(parts[1])
                y = int(parts[2])

                color = None
                zone = Zone_class.normal
                max_drones = 1

                if len(parts) > 3:
                    meta_data = parts[3].strip("[]").split()
                    for item in meta_data:
                        key, value = item.split("=", 1)
                    
                        if key == "zone":
                            zone = Zone_class(value)
                        elif key == "color":
                            color = value
                        elif key == "max_drones":
                            max_drones = int(value)
                        else:
                            raise ValueError(f"Unknown data: {key}")

                    

                hubs[name] = {
                            "type": hub_type,
                            "x": x,
                            "y": y,
                            "zone": zone,
                            "color": color,
                            "max_drones": max_drones
                            }

            elif line.startswith("connection:"):
                connection_data = line.split(":", 1)[1].strip()
                
                if "[" in connection_data:
                    connection_data, extra_info = connection_data.split("[", 1)
                    extra_info = extra_info.strip("]")
                else:
                    extra_info = None
                hub_a, hub_b = connection_data.split("-", 1)
                hub_b = hub_b.strip()       
                max_link_capacity = 1
                if extra_info:    
                    if extra_info.startswith("max_link_capacity="):
                        value = extra_info.split("=", 1)[1]
                        max_link_capacity = int(value)
                    else:
                        raise ValueError(f"Unknown input: {key}")

                connection_list.append(
                                    {"from": hub_a,
                                        "to": hub_b,
                                        "max_link_capacity": max_link_capacity})
    return(hubs, connection_list)

def get_zone_cost(zone):
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


def build_graph(hubs, connection_list):
    graph = {}

    for hub_name in hubs:
        graph[hub_name] = {}

    for connection in connection_list:
        hub_a = connection["from"]
        hub_b = connection["to"]
        capacity = connection["max_link_capacity"]

        #print("hub_a", hub_a)
        #print("hub_b", hub_b)

        cost_a_to_b = get_zone_cost(hubs[hub_b]["zone"])
        cost_b_to_a = get_zone_cost(hubs[hub_a]["zone"])

        if cost_a_to_b is not None:
            graph[hub_a][hub_b] = {
                "cost": cost_a_to_b,
                "capacity": capacity
            }
        
        if cost_b_to_a is not None:
            graph[hub_b][hub_a] = {
                "cost": cost_b_to_a,
                "capacity": capacity
            }
    return(graph)


def dijkstra(graph, start, goal):
    print(graph)

    if goal == start:
        return (0)

    distances = {}
    previous = {}
    unvisited = []
    for key in graph:
        if key == start:
            distances[key] = 0
            unvisited.append(key)
        else:
            distances[key]= float("inf")
            unvisited.append(key)

    print("\n", graph[start], "\n")
    #   print(distances.keys())

    i = 0

    from_node = start

    while (unvisited != []):
        unvisited.remove(from_node)
        print("from", from_node)
        print("options", graph[from_node])

        for item in graph[from_node]:
            if distances[item] > distances[from_node] + graph[from_node][item]["cost"]:
                distances[item] = distances[from_node] + graph[from_node][item]["cost"]
                previous[item] = from_node

        min_cost_list = []
        for item in list(distances.keys()):
            if item in unvisited:
                min_cost_list.append(distances[item])

        min_cost = min(min_cost_list)

        if min_cost == float("inf"):
            break

        min_value = None

        for item in list(distances.keys()):
            if distances[item] == min_cost and item in unvisited:
                min_value = item
                break

        #print("min cost", min_cost)
        #print("Min_value", min_value)

        #distances[min_value] = min_cost + distances[from_node]

        #print("distances", distances)
        #print("unvisited", unvisited)

        from_node = min_value
        if from_node == goal:
            break


    print("previous", previous)

    if distances[goal] == float("inf"):
        return(float(inf))

    reverse_path = [goal]
    point = goal

    while (start not in reverse_path):
        next_point = previous[point]
        reverse_path.append(next_point)
        point = next_point

    path = reverse_path[:: -1]


    print("path", path)
    return(distances[goal])


if __name__ == "__main__":

    entry_file = sys.argv[1]

    parsing = parser(entry_file)

    hubs = parsing[0]

    #print("hubs:", hubs)

    connection_list = parsing[1]

    #print("connection list:", connection_list)

    graph = build_graph(hubs, connection_list)

    print("graph:", graph)

    for item in hubs:
        if hubs[item]["type"] == "start_hub":
            start = item
        if hubs[item]["type"] == "end_hub":
            goal = item
        

    dijkstra(graph, start, goal)
