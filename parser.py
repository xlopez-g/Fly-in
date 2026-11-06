#!/usr/bin/env python3
"""Map parser module for the Fly-in drone routing simulation.

Reads map text files, validates syntax, parses metadata (zone types, colors,
capacities), and builds structured entities while ensuring strict error
handling.
"""

from models import HUB_TYPE, Zone_class, Hub, Connection


def validate_connections(connection_list: list[Connection],
                         hubs: dict[str, Hub]) -> None:

    hubs_list = list(hubs.keys())
    hub_a_hub_b_list: list[tuple[str, str]] = []

    for connection in connection_list:

        hub_a = connection.hub_a
        hub_b = connection.hub_b
        pair = (min(hub_a, hub_b), max(hub_a, hub_b))
        hub_a_hub_b_list.append(pair)

        if hub_a not in hubs_list:
            raise ValueError(f"{connection.hub_a} not in hubs")
        if hub_b not in hubs_list:
            raise ValueError(f"{connection.hub_b} not in hubs")

    if len(hub_a_hub_b_list) != len(set(hub_a_hub_b_list)):
        raise ValueError("Duplicated connections")


def parse_hub(hubs: dict[str, Hub],
              hub_type_entry: str,
              hub_data: str) -> None:

    max_drones = 1

    if hub_type_entry == "start_hub":
        hub_type = HUB_TYPE.start_hub
        max_drones = 999999

    elif hub_type_entry == "hub":
        hub_type = HUB_TYPE.hub

    elif hub_type_entry == "end_hub":
        hub_type = HUB_TYPE.end_hub
        max_drones = 999999

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

    hub = Hub(hub_type=hub_type,
              name=name,
              x=x,
              y=y,
              zone=zone,
              color=color,
              max_drones=max_drones)

    hubs[hub.name] = hub


def parse_connection(connection_list: list[Connection],
                     connection_data: str) -> None:

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


def parser(file_path: str) -> tuple[int, dict[str, Hub], list[Connection]]:
    """Parse a map file and validate all network and drone constraints.

    Args:
        file_path: Path to the input map text file.

    Returns:
        A tuple containing (nb_drones, hubs_dict, connections_list).

    Raises:
        ValueError: On any syntax error, unknown metadata, invalid capacity,
            missing or non-unique start/end hubs, or duplicated connections.
    """

    nb_drones: None | int = None
    hubs: dict[str, Hub] = {}
    connection_list: list[Connection] = []

    start_hub_quantity = 0
    end_hub_quantity = 0
    first_line = 1

    with open(file_path, "r") as entry_file:

        for numline in enumerate(entry_file, start=1):

            try:
                index, line = numline
                line = line.strip()

                if not line or line.startswith("#"):
                    if index == first_line:
                        first_line += 1
                    continue

                if line.startswith("nb_drones:"):
                    if index == first_line:
                        nb_drones = int(line.split(":")[1].strip())
                    else:
                        raise ValueError("nb_drones must be on the first line")

                elif line.startswith(("start_hub:", "hub:", "end_hub:")):
                    hub_type_entry, hub_data = line.split(":", 1)

                    parse_hub(hubs, hub_type_entry, hub_data)

                    if hub_type_entry == "start_hub":
                        start_hub_quantity += 1

                    elif hub_type_entry == "end_hub":
                        end_hub_quantity += 1

                elif line.startswith("connection:"):
                    connection_data = line.split(":", 1)[1].strip()

                    parse_connection(connection_list, connection_data)

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
        raise ValueError("start hub not exist or not unique")

    if end_hub_quantity != 1:
        raise ValueError("End hub not exist or not unique")

    validate_connections(connection_list, hubs)

    return (nb_drones, hubs, connection_list)
