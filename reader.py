#!/usr/bin/env python3

from enum import Enum

from pydantic import BaseModel, Field, ValidationError

import sys


class Zone_class(Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class HUB_TYPE(Enum):
    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"


class Hub(BaseModel):
    hub_type: HUB_TYPE
    name: str = Field(min_length=3, max_length=30)
    x: int
    y: int
    zone: Zone_class = Zone_class.normal
    color: str | None = Field(default=None, min_length=3, max_length=15)
    max_drones: int = Field(default=1, ge=1)


class Connection(BaseModel):
    hub_a: str = Field(min_length=3, max_length=30)
    hub_b: str = Field(min_length=3, max_length=30)
    max_link_capacity: int = Field(default=1, ge=0)


class Drone(BaseModel):
    id: str
    path: list[str]
    path_index: int
    in_transit: bool = False
#    remaining_turns: int

    def propose_move(self) -> None | int:
        if self.path_index == len(self.path) - 1:
            return None
        else:
            return self.path[self.path_index + 1]

    def apply_move(self) -> None:
        if self.path_index < len(self.path) - 1:
            self.path_index += 1
#           self.remaining_turns -= 1

    def has_arrived(self) -> bool:
        if self.path_index == len(self.path) - 1:
            return (True)
        else:
            return False


class Hub_Reservation(BaseModel):

    hub_name: str
    turn: int
    drone_number: int


class Connection_Reservation(BaseModel):

    from_hub: str
    to_hub: str
    turn: int
    drone_number: int


class Reservation_Table(BaseModel):
    #Hub diccionary creation(name, turn): drone number
    hub_occupancy: dict[tuple[str, int], int] = Field(default_factory=dict)

    #Connection dictionary creation (drom_hub. to_hub, turn): dron number
    connection_occupancy: dict[tuple[str, str, int], int] = Field(default_factory=dict)
    
    def is_hub_available(self, hub_name, turn, max_drones) -> bool:
        current_drones = self.hub_occupancy.get((hub_name, turn), 0)
        
        if current_drones < max_drones:
            return True

        return False


    def is_connection_available(self, from_hub, to_hub, turn, max_link_capacity) -> bool:

        connection_check = (from_hub, to_hub, turn)
        connection_back = (to_hub, from_hub, turn)
        
        current_drones = (self.connection_occupancy.get(connection_check, 0)
                          + self.connection_occupancy.get(connection_back, 0))

        if (current_drones < max_link_capacity):
            return True

        return False


    def reserve_hub(self, hub_name, turn) -> None:
        hub_key = (hub_name, turn)
        current_drones = self.hub_occupancy.get(hub_key, 0)

        self.hub_occupancy[hub_key] = current_drones + 1


    def reserve_connection(self, from_hub, to_hub, turn) -> None:
        connection_key = (from_hub, to_hub, turn)
        current_drones = self.connection_occupancy.get(connection_key, 0)

        self.connection_occupancy[connection_key] = current_drones + 1


def parser(read_file: str):

    nb_drones = 0
    hubs: dict[str, Hub] = {}
    connection_list: list[Connection] = []

    with open(read_file, "r") as entry_file:

        for line in entry_file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("nb_drones:"):
                nb_drones = int(line.split(":")[1].strip())

            elif line.startswith(("start_hub:", "hub:", "end_hub:")):
                hub_type, hub_data = line.split(":", 1)
                if hub_type == "start_hub":
                    hub_type = HUB_TYPE.start_hub
                elif hub_type == "hub":
                    hub_type = HUB_TYPE.hub
                elif hub_type == "end_hub":
                    hub_type = HUB_TYPE.end_hub

                parts = hub_data.strip().split(None, 3)

                name = parts[0]
                x = int(parts[1])
                y = int(parts[2])

                color = None
                zone = Zone_class.normal
                max_drones = 1

                if len(parts) > 3:
                    meta_data = parts[3].strip("[]").split()
                    for node in meta_data:
                        key, value = node.split("=", 1)

                        if key == "zone":
                            zone = Zone_class(value)
                        elif key == "color":
                            color = value
                        elif key == "max_drones":
                            max_drones = int(value)
                        else:
                            raise ValueError(f"Unknown data: {key}")

                hub = Hub(hub_type=hub_type,
                          name=name,
                          x=x,
                          y=y,
                          zone=zone,
                          color=color,
                          max_drones=max_drones)

                hubs[hub.name] = hub

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
                        raise ValueError(f"Unknown input: {extra_info}")

                connection = Connection(hub_a=hub_a,
                                        hub_b=hub_b,
                                        max_link_capacity=max_link_capacity)

                connection_list.append(connection)

    #print("\nconnection class list", connection_list)
    return (nb_drones, hubs, connection_list)


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
        hub_a = connection.hub_a
        hub_b = connection.hub_b
        capacity = connection.max_link_capacity

        #print("hub_a", hub_a)
        #print("hub_b", hub_b)

        cost_a_to_b = get_zone_cost(hubs[hub_b].zone)
        cost_b_to_a = get_zone_cost(hubs[hub_a].zone)

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
    return (graph)


def create_drones(nb_drones: int, path: list[str]) -> list[Drone]:

    if nb_drones < 1:
        raise ValueError("Invalid input for drone numbers")

    drone_list = []

    for i in range(0, nb_drones):
        new_drone = Drone(id=f"D{i + 1}",
                          path=path.copy(),
                          path_index=0,
                          in_transit=False)
                            #remaining_turns=len(path))
        drone_list.append(new_drone)

    return drone_list


def dijkstra(graph, start, goal, max_turn):

    if goal == start:
        return ([start], 0)

    queue_list = [(start, 0)]

    distances = {}
    previous = {}
    unvisited = []

    turn = 0
    for turn in range(max_turn):
        for key in graph:
            unvisited.append((key, turn))
            distances[(key, turn)] = float("inf")
            if key == start and turn == 0:
                distances[(key, 0)] = 0

    from_node = (start, 0)
    print("from node", from_node)

    final_turn = None

    while (unvisited != []):
        turn = from_node[1]
        unvisited.remove(from_node)

        if from_node[0] == (goal):
            final_turn = from_node[1]
            break

        print("unvisited", unvisited)
        for next_node in graph[from_node[0]]:
            cost_node = graph[from_node[0]][next_node]["cost"]
            #print("cost node", cost_node)
            if (distances[(next_node, turn + cost_node)] > distances[from_node] + cost_node):
                distances[(next_node, turn + cost_node)] = distances[from_node] + cost_node
                previous[(next_node, turn + cost_node)] = from_node

        min_cost_list = []
        min_cost = float("inf")
        current_state = None
        print("distances", distances)

        min_tuple_list = list(distances.keys())
        
        for (node, turn_i) in min_tuple_list:
            #print("ffff", (node, turn_i), "---", distances[(node, turn_i)])
            if (node, turn_i) in unvisited and distances[(node, turn_i)] < min_cost:
                min_cost = distances[(node, turn_i)]
                current_state = (node, turn_i)

        print("mincost list", current_state)
#        min_cost = min(min_cost_list)

        if current_state is None or min_cost == float("inf"):
            break

#        min_value = None

#        for node in min_tuple_list:
 #           if distances[(node, turn)] == min_cost and node in unvisited_next_turn:
  #              min_value = node
   #             break
        from_node = current_state
        print("from node", from_node)


    if distances[goal, turn] == float("inf"):
        return ([start], float("inf"))

    reverse_path = [(goal, final_turn)]
    point = (goal, final_turn)

    while ((start, 0) not in reverse_path):
        next_point = previous[point]
        reverse_path.append(next_point)
        point = next_point

    path = reverse_path[:: -1]

    print("path", path)
    #print("distance total", distances[goal])
    return (path, distances[goal, final_turn])


def all_drones_arrived(drones) -> bool:
    arrived = True

    for drone in drones:
        if drone.path_index != len(drone.path) - 1:
            arrived = False

    return (arrived)


def simulate(drones, graph):
    turn = 0
    connection_usage = {}

    drone = drones[0]

    length = len(drone.path)

    for i in range(length - 2):
        connection_usage[drone.path[i], drone.path[i + 1]] = 0

    while not all_drones_arrived(drones):

        for i in range(len(drone.path) - 1):
            connection_usage[drone.path[i], drone.path[i + 1]] = 0

        for drone in drones:
            if drone.in_transit:
                drone.in_transit = False
                current_hub = drone.path[drone.path_index]
                next_hub = drone.path[drone.path_index + 1]
                connection_usage[(current_hub, next_hub)]

            else:
                current_hub = drone.path[drone.path_index]
                next_hub = drone.propose_move()

                if (drone.propose_move()
                    and (connection_usage[(current_hub, next_hub)] < graph[current_hub][next_hub]["capacity"])):
                    
                    drone.apply_move()
                    connection_usage[current_hub, next_hub] += 1
                    print(f"{drone.id}-{drone.path[drone.path_index]}",
                          end=" ")

                    if graph[current_hub][next_hub]["cost"] == 2:
                        drone.in_transit = True

        print()
        turn += 1
        #print(f"|||{current_hub} - {next_hub}", graph[current_hub][next_hub]["capacity"])
        #print(f"\nturn {turn}: drones{drones}")
        #print("cccccc", connection_usage)
#        propose movements
#        resolve conflicts
#        apply allowed movements
#        update states
#        show each turn result


if __name__ == "__main__":

    if sys.argv[1] is None:
        raise ValueError("missed argument")

    entry_file = sys.argv[1]

    parsing = parser(entry_file)

    nb_drones = parsing[0]

    #print("nb drones", nb_drones)

    hubs = parsing[1]

    #print("hubs:", hubs)

    connection_list = parsing[2]

    #print("\n\nconnection list:", connection_list)

    graph = build_graph(hubs, connection_list)

    print("graph:", graph)

    for node in hubs:
        if hubs[node].hub_type == HUB_TYPE.start_hub:
            start = node
        if hubs[node].hub_type == HUB_TYPE.end_hub:
            goal = node
    print("start:", start)
    path = dijkstra(graph, start, goal, 20)[0]
    distance = dijkstra(graph, start, goal, 20)[1]
    #dijkstra(graph, "maze_a2", goal)

    drones = create_drones(nb_drones, path)

    simulate(drones, graph)

    #print("drone list", drones)

