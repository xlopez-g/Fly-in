#!/usr/bin/env python3

nb_drones = 0
hubs = {}
connection_list = []

with open("map.txt", "r") as entry_file:

    for line in entry_file:
        line = line.strip()
        
        if not line or line.startswith("#"):
            continue

        if line.startswith("nb_drones:"):
            nb_drones = int(line.split(":")[1].strip())

        elif line.startswith(("start_hub:", "hub:", "end_hub:")):
            hub_type, hub_data = line.split(":", 1)
            parts = hub_data.strip().split()

            name = parts[0]
            x = int(parts[1])
            y = int(parts[2])

            color = None
            if len(parts) > 3:
                color = parts[3].replace("[color=", "").replace("]", "")

            hubs[name] = {
                          "type": hub_type,
                          "x": x,
                          "y": y,
                          "color": color
                          }

        elif line.startswith("connection:"):
            connection_data = line.split(":", 1)[1].strip()
            hub_a, hub_b = connection_data.split("-", 1)            
            
            connection_list.append((hub_a, hub_b))

print(nb_drones)

print(hubs)

print(connection_list)


