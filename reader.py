#!/usr/bin/env python3

from enum import Enum

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

    distances = {}
    previous = {}
    unvisited = {}

    for key in graph:
        if key == start:
            distances[key] = 0
            unvisited[key] = False
        else:
            distances[key]= float("inf")
            unvisited[key] = True

    print("\n", graph[start], "\n")
    neighbour_list = []
    #   print(distances.keys())

    i = 0
    while (i < 3):
        distances_list = list(distances.values())
        print("min", min(distances_list))
            

        for key in graph[start]:
            neighbour_list.append(key)
            cost = graph[start][key]["cost"]
            if cost < distances[key]:
                distances[key] = cost
            previous[key] = start

        i += 1



    print("initial distances", distances)
    print("previous", previous)
    print("unvisited", unvisited)




if __name__ == "__main__":
    parsing = parser("config.txt")

    hubs = parsing[0]

    #print("hubs:", hubs)

    connection_list = parsing[1]

    #print("connection list:", connection_list)

    graph = build_graph(hubs, connection_list)

    print("graph:", graph)

    dijkstra(graph, "hub", "goal")
