#!/usr/bin/env python3

from models import HUB_TYPE, Zone_class, Hub, Connection


def parser(file_path: str) -> tuple[int, dict[str, "Hub"], list["Connection"]]:

    nb_drones: None | int = None
    hubs: dict[str, Hub] = {}
    connection_list: list[Connection] = []

    start_hub_quantity = 0
    end_hub_quantity = 0
    first_index = 1

    with open(file_path, "r") as entry_file:

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

                    hub_type_entry, hub_data = line.split(":", 1)
                    if hub_type_entry == "start_hub":
                        hub_type = HUB_TYPE.start_hub
                        max_drones = 10000
                        start_hub_quantity += 1

                    elif hub_type_entry == "hub":
                        hub_type = HUB_TYPE.hub

                    elif hub_type_entry == "end_hub":
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
