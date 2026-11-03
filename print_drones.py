#!/usr/bin/env python3

from models import Hub, Connection, Drone


def print_drones(drone_list: list[Drone],
                 hubs: dict[str, "Hub"],
                 connection_list: list[Connection]) -> None:

    final_turn = drone_list[-1].path[-1][1]

    all_step: str = ""

    COLORS = {"RED": "\033[31m", "GREEN": "\033[32m",
              "YELLOW": "\033[33m", "BLUE": "\033[34m",
              "GREY": "\033[90m", "RESET": "\033[0m",
              "PURPLE": "\033[35m", "MAROON": "\033[38;5;52m",
              "ORANGE": "\033[38;5;208m", "BROWN": "\033[33m",
              "GOLD": "\033[38;5;220m", "DARKRED": "\033[38;5;88m",
              "CRIMSON": "\033[38;5;161m", "RAINBOW": "\033[34m",
              "CYAN": "\033[36m", "LIME": "\033[92m", "MAGENTA": "\033[35m"}

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

                        phrase = (f"{drone.id}-{drone.path[step][0].name}")
                        if first_written_drone is True:
                            all_step += phrase
                            first_written_drone = False
                            color = drone.path[step][0].color
                            if color is not None:
                                color = color.upper()
                            if color in COLORS:
                                print(f"{COLORS[color]}",
                                      phrase,
                                      f"{COLORS["RESET"]}",
                                      end="", sep="")

                            else:
                                print(phrase, end="")

                        else:
                            all_step += " " + phrase
                            color = drone.path[step][0].color
                            if color is not None:
                                color = color.upper()
                            if color in COLORS:
                                print(f"{COLORS[color]} {phrase}"
                                      f"{COLORS["RESET"]}",
                                      end="", sep="")

                            else:
                                print(" " + phrase, end="")

                if drone.path[step][1] == turn - 1:
                    if (step + 1 < len(drone.path) and
                        (drone.path[step + 1][1] - 1
                         != drone.path[step][1])):

                        from_h = drone.path[step][0]
                        to_h = drone.path[step + 1][0]
                        phrase = f"{drone.id}-{from_h.name}-{to_h.name}"
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
