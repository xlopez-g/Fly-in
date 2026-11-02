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


class Reservation_Table(BaseModel):
    #Hub diccionary creation(name, turn): drone number
    hub_occupancy: dict[tuple[str, int], int] = Field(default_factory=dict)

    #Connection dictionary creation (drom_hub. to_hub, turn): dron number
    connection_occupancy: dict[tuple[str, str, int], int] = Field(default_factory=dict)

    def is_hub_available(self,
                         hub_name: str,
                         turn: int,
                         max_drones: int) -> bool:
        current_drones = self.hub_occupancy.get((hub_name, turn), 0)

        if current_drones < max_drones:
            return True

        return False

    def is_connection_available(self,
                                from_hub: str,
                                to_hub: str,
                                turn: int,
                                max_link_capacity: int) -> bool:

        connection_check = (from_hub, to_hub, turn)
        connection_back = (to_hub, from_hub, turn)

        current_drones = (self.connection_occupancy.get(connection_check, 0)
                          + self.connection_occupancy.get(connection_back, 0))

        if (current_drones < max_link_capacity):
            return True

        return False

    def reserve_hub(self, hub_name: str, turn: int) -> None:
    
        hub_key = (hub_name, turn)
        current_drones = self.hub_occupancy.get(hub_key, 0)

        self.hub_occupancy[hub_key] = current_drones + 1

    def reserve_connection(self, from_hub: str, to_hub: str,
                           turn: int) -> None:
        connection_key = (from_hub, to_hub, turn)
        current_drones = self.connection_occupancy.get(connection_key, 0)

        self.connection_occupancy[connection_key] = current_drones + 1


def parser(read_file: str):

    nb_drones: None | int = None
    hubs: dict[str, Hub] = {}
    connection_list: list[Connection] = []

    start_hub_quantity = 0
    end_hub_quantity = 0
    first_index = 1

    with open(read_file, "r") as entry_file:

        for numline in enumerate(entry_file, start=1):

            try:
                index, line = numline
                line = line.strip()

                if not line or line.startswith("#"):
                    if index == first_index:
                        first_index += 1
                    continue

                if line.startswith("nb_drones:"):
                    if index == first_index:
                        nb_drones = int(line.split(":")[1].strip())
                    else:
                        raise ValueError("nb_drones must be on the first line")

                elif line.startswith(("start_hub:", "hub:", "end_hub:")):
                    max_drones = 1

                    hub_entry, hub_data = line.split(":", 1)
                    if hub_entry == "start_hub":
                        hub_type = HUB_TYPE.start_hub
                        max_drones = 10000
                        start_hub_quantity += 1

                    elif hub_entry == "hub":
                        hub_type = HUB_TYPE.hub

                    elif hub_entry == "end_hub":
                        hub_type = HUB_TYPE.end_hub
                        max_drones = 10000
                        end_hub_quantity += 1

                    parts = hub_data.strip().split(None, 3)

                    name = parts[0]
                    x = int(parts[1])
                    y = int(parts[2])

                    color = None
                    zone = Zone_class.normal

                    if name in list(hubs.keys()):
                        raise ValueError("Duplicated name of hub")

                    if len(parts) > 3:
                        meta_data = parts[3].strip("[]").split()
                        for node in meta_data:
                            key, value = node.split("=", 1)

                            if key == "zone":
                                zone = Zone_class(value)
                            elif key == "color":
                                color = value
                            elif (key == "max_drones"):
                                start_type = HUB_TYPE.start_hub
                                end_type = HUB_TYPE.end_hub
                                if not (hub_type == start_type
                                        or hub_type == end_type):
                                    max_drones = int(value)

                            else:
                                raise ValueError(f"Unknown data: {key}")

                    hub = Hub(hub_type=HUB_TYPE,
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
                        extra_info = connection_data.split("[", 1)[1]
                        connection_data = connection_data.split("[", 1)[0]
                        extra_info = extra_info.strip("]")
                    else:
                        extra_info = None
                    hub_a, hub_b = connection_data.split("-", 1)
                    hub_b = hub_b.strip()
                    max_l_cap = 1
                    if extra_info:
                        if extra_info.startswith("max_link_capacity="):
                            value = extra_info.split("=", 1)[1]
                            max_l_cap = int(value)
                        else:
                            raise ValueError(f"Unknown input: {extra_info}")

                    connection = Connection(hub_a=hub_a,
                                            hub_b=hub_b,
                                            max_link_capacity=max_l_cap)

                    connection_list.append(connection)

                else:
                    raise ValueError("Unrecognized syntax"
                                     f" or command on line {index}: '{line}'")

            except Exception as e:
                raise ValueError(f"Error on  line {index}: {e}")

    if nb_drones is None:
        raise ValueError("Number of drones not found")

    if nb_drones <= 0:
        raise ValueError("Invalid number of drones, "
                         "it must be a positive integer")

    if start_hub_quantity != 1:
        raise ValueError("start hub not unique")

    if end_hub_quantity != 1:
        raise ValueError("End hub not unique")

    hubs_list = list(hubs.keys())
    len_hubs = len(hubs_list)
    len_set_hubs = len(set(hubs_list))
    if len_hubs != len_set_hubs:
        raise ValueError("Duplicated value on hubs")

#    len_connection = len(connection_list)
#    len_set_connection = len(set(connection_list))
#    if len_connection != len_set_connection:
#        raise ValueError("Duplicated value on zones")

    hub_a_list = []
    hub_b_list = []
    hub_a_hub_b_list = []

    for connection in connection_list:
        hub_a_list.append(connection.hub_a)
        hub_b_list.append(connection.hub_b)
        hub_a = connection.hub_a
        hub_b = connection.hub_b
        hub_a_hub_b_list.append(tuple(sorted([hub_a, hub_b])))
        if connection.hub_a not in hubs_list:
            raise ValueError(f"{connection.hub_a} not in hubs")
        if connection.hub_b not in hubs_list:
            raise ValueError(f"{connection.hub_b} not in hubs")

    if len(hub_a_hub_b_list) != len(set(hub_a_hub_b_list)):
        raise ValueError("Duplicated connections")

    return (nb_drones, hubs, connection_list)


def get_zone_cost(zone) -> int:
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


def build_graph(hubs, connection_list) -> dict[tuple[str, str], (int, int)]:
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


def print_drones(drone_list, hubs, connection_list) -> None:

    final_turn = drone_list[-1].path[-1][1]

    all_step: str = ""

    COLORS = {"RED": "\033[31m", "GREEN": "\033[32m",
              "YELLOW": "\033[33m", "BLUE": "\033[34m",
              "GREY": "\033[90m", "RESET": "\033[0m",
              "PURPLE": "\033[35m", "MAROON": "\033[38;5;52m",
              "ORANGE": "\033[38;5;208m", "BROWN": "\033[33m",
              "GOLD": "\033[38;5;220m", "DARKRED": "\033[38;5;88m",
              "CRIMSON": "\033[38;5;161m", "RAINBOW": "\033[34m"}

    for turn in range(1, final_turn + 2):
        first_written_drone = True
        if turn != final_turn + 1:
            print("turn", turn)

        for drone in drone_list:
            for step in range(len(drone.path)):

                if drone.path[step][1] == turn:
                    if (step > 0
                            and (drone.path[step][0]
                                 != drone.path[step - 1][0])):

                        phrase = (f"{drone.id}-{drone.path[step][0]}")
                        if first_written_drone is True:
                            all_step += phrase
                            first_written_drone = False
                            color = hubs[drone.path[step][0]].color
                            color = color.upper()
                            if color in COLORS:
                                print(f"{COLORS[color]}", phrase, f"{COLORS["RESET"]}", end="", sep="")
                            else:
                                print(phrase, end="")

                        else:
                            all_step += " " + phrase
                            color = hubs[drone.path[step][0]].color
                            color = color.upper()
                            if color in COLORS:
                                print(f"{COLORS[color]}", phrase, f"{COLORS["RESET"]}", end="", sep="")
                            else:
                                print(" " + phrase, end="")

                if drone.path[step][1] == turn - 1:
                    if (step + 1 < len(drone.path) and
                        (drone.path[step + 1][1] - 1
                         != drone.path[step][1])):

                        phrase = f"{drone.id}-{drone.path[step][0]}-{drone.path[step + 1][0]}"
                        if first_written_drone is True:
                            all_step += phrase
                            first_written_drone = False
                            print(phrase, end="")
                        else:
                            all_step += " " + phrase
                            print(" " + phrase, end="")

        if turn < final_turn:
            all_step += "\n"
        if turn == final_turn:
            print()
        if turn == final_turn + 1:
            print(all_step)
        else:
            try:
                input()
            except KeyboardInterrupt:
                print("Out of the program")
                break


def program(entry_file: str) -> None:

    try:
        parsing = parser(entry_file)
    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(1)

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
    c_occupancy = {}
    reservation_table = Reservation_Table(hub_occupancy=hub_occupancy,
                                          connection_occupancy=c_occupancy)

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
