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
    name: str = Field(min_length=3,
                      max_length=30,
                      pattern=r"^[^\s\-]+$")
    x: int
    y: int
    zone: Zone_class = Zone_class.normal
    color: str | None = Field(default=None, min_length=3, max_length=15)
    max_drones: int = Field(default=1, gt=0)


class Connection(BaseModel):
    hub_a: str = Field(pattern=r"^[^\s\-]+$")
    hub_b: str = Field(pattern=r"^[^\s\-]+$")
    max_link_capacity: int = Field(default=1, gt=0)


class Drone(BaseModel):
    id: str
    path: list[tuple[str, int]]
    path_index: int

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

    def is_connection_available(self,
                                from_hub,
                                to_hub,
                                turn,
                                max_link_capacity) -> bool:

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

    nb_drones: int = None
    hubs: dict[str, Hub] = {}
    connection_list: list[Connection] = []

    start_hub_quantity = 0
    end_hub_quantity = 0

    with open(read_file, "r") as entry_file:

        for line in entry_file:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith("nb_drones:"):
                nb_drones = int(line.split(":")[1].strip())
                if nb_drones == None or nb_drones < 0:
                    raise ValueError("Invalid nb_drones value,"
                                     "it must be positive")

            elif line.startswith(("start_hub:", "hub:", "end_hub:")):
                max_drones = 1

                hub_type, hub_data = line.split(":", 1)
                if hub_type == "start_hub":
                    hub_type = HUB_TYPE.start_hub
                    max_drones = sys.maxint
                    start_hub_quantity += 1

                elif hub_type == "hub":
                    hub_type = HUB_TYPE.hub

                elif hub_type == "end_hub":
                    hub_type = HUB_TYPE.end_hub
                    max_drones = sys.maxint
                    end_hub_quantity += 1

                if start_hub_quantity > 1:
                    raise ValueError("start hub not unique")

                if end_hub_quantity > 1:
                    raise ValueError("End hub not unique")

                parts = hub_data.strip().split(None, 3)

                name = parts[0]
                x = int(parts[1])
                y = int(parts[2])

                color = None
                zone = Zone_class.normal

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


def create_drones(nb_drones: int, path: list[tuple[str, int]]) -> list[Drone]:

    if nb_drones < 1:
        raise ValueError("Invalid input for drone numbers")

    drone_list = []

    for i in range(0, nb_drones):
        new_drone = Drone(id=f"D{i + 1}",
                          path=path.copy(),
                          path_index=0)
        drone_list.append(new_drone)

    return drone_list


def dijkstra(graph, hubs, connection_list, reservation_table, start, goal):

    if goal == start:
        return ([(start, 0)], 0)

    distances = {}
    previous = {}
    unvisited = set()

    from_node = (start, 0)

    distances[(start, 0)] = 0
    unvisited.add((start, 0))

    final_turn = None

    while (unvisited):
        turn = from_node[1]
        unvisited.remove(from_node)

        if from_node[0] == (goal):
            final_turn = from_node[1]
            break

        options_to_check = []
        options_to_check.append(from_node[0])
        for node in list(graph[from_node[0]].keys()):
            options_to_check.append(node)

        for next_node in options_to_check:
            if next_node == from_node[0]:
                cost_node = 1
                max_drones = hubs[from_node[0]].max_drones

                if not (reservation_table.is_hub_available(from_node[0], turn + cost_node, max_drones)):
                    #print("wait not ok")
                    continue

            else:
                #print("frm node", from_node, "to", next_node)
                cost_node = graph[from_node[0]][next_node]["cost"]
                max_drones = hubs[next_node].max_drones
                #print(f"{next_node} maxdrones {max_drones}")

                if not (reservation_table.is_hub_available(next_node, turn + cost_node, max_drones)):
                    #print(f"from {from_node} {next_node} hub not ok")
                    continue

                max_link_capacity = graph[from_node[0]][next_node]["capacity"]

                if not (reservation_table.is_connection_available(from_node[0], next_node, turn + cost_node, max_link_capacity)):
                    #print(f"{from_node[0]} - {next_node} {turn + cost_node} connection not available ")
                    continue
                if (cost_node == 2 and
                    not (reservation_table.is_connection_available(from_node[0], next_node, turn + cost_node - 1, max_link_capacity))):
                    #print(f"{from_node[0]} - {next_node} {turn + cost_node} connection not available ")
                    continue

            distance_next_node = distances.get((next_node, turn + cost_node), float("inf"))
            new_posible_distance = distances[from_node] + cost_node
            #print("cost node", cost_node)
            if (distance_next_node > new_posible_distance):
                distances[(next_node, turn + cost_node)] = new_posible_distance
                previous[(next_node, turn + cost_node)] = from_node
                unvisited.add((next_node, turn + cost_node))
        #min_cost_list = []
        min_cost = float("inf")
        current_state = None
        #print("distances", distances)

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
        return ([start], float("inf"))

    reverse_path = [(goal, final_turn)]
    point = (goal, final_turn)

    while ((start, 0) not in reverse_path):
        next_point = previous[point]
        reverse_path.append(next_point)
        point = next_point

    path = reverse_path[:: -1]

    return (path, distances[(goal, final_turn)])


def all_drones_arrived(drones) -> bool:
    arrived = True

    for drone in drones:
        if drone.path_index != len(drone.path) - 1:
            arrived = False

    return (arrived)


if __name__ == "__main__":

    if sys.argv[1] is None:
        raise ValueError("missed argument")

    entry_file = sys.argv[1]

    parsing = parser(entry_file)

    nb_drones = parsing[0]

    hubs = parsing[1]

    print("hubs:", hubs)

    connection_list = parsing[2]

    print("\n\nconnection list:", connection_list)

    graph = build_graph(hubs, connection_list)

    print("graph:", graph)

    for node in hubs:
        if hubs[node].hub_type == HUB_TYPE.start_hub:
            start = node
        if hubs[node].hub_type == HUB_TYPE.end_hub:
            goal = node

    hub_occupancy = {}
    connection_occupancy = {}
    reservation_table = Reservation_Table(hub_occupancy=hub_occupancy,
                                          connection_occupancy=connection_occupancy)

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
#        print("reservation table", reservation_table)

    print("drone list", drone_list)

    final_turn = drone_list[-1].path[-1][1]

    print("final turn", final_turn, drone_list[-1].path[-1][1])

    for turn in range(0, final_turn + 1):
        print("turn", turn)
        for drone in drone_list:
            for time in range(len(drone.path)):
                if drone.path[time][1] == turn:
                    if (time > 0
                            and (drone.path[time][0]
                                 != drone.path[time - 1][0])):

                        print(f"{drone.id}-{drone.path[time][0]}", end=" ")
        if turn == final_turn:
            print()
            break
        else:
            try:
                input()
            except KeyboardInterrupt:
                print("Out of the program")
                break
