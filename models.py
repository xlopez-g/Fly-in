#!/usr/bin/env python3

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


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
    model_config = ConfigDict(frozen=True)

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
    path: list[tuple[Hub, int]]
    path_index: int


class Reservation_Table(BaseModel):
    #Hub diccionary creation(name, turn): drone number
    hub_load: dict[tuple[Hub, int], int] = Field(default_factory=dict)

    #Connection dictionary creation (drom_hub. to_hub, turn): dron number
    conn_load: dict[tuple[Hub, Hub, int], int] = Field(default_factory=dict)

    def is_hub_available(self,
                         hub_name: Hub,
                         turn: int,
                         max_drones: int) -> bool:
        current_drones = self.hub_load.get((hub_name, turn), 0)

        if current_drones < max_drones:
            return True

        return False

    def is_connection_available(self,
                                from_hub: Hub,
                                to_hub: Hub,
                                turn: int,
                                max_link_capacity: int) -> bool:

        connection_check = (from_hub, to_hub, turn)
        connection_back = (to_hub, from_hub, turn)

        current_drones = (self.conn_load.get(connection_check, 0)
                          + self.conn_load.get(connection_back, 0))

        if (current_drones < max_link_capacity):
            return True

        return False

    def reserve_hub(self, hub_name: Hub, turn: int) -> None:

        hub_key = (hub_name, turn)
        current_drones = self.hub_load.get(hub_key, 0)

        self.hub_load[hub_key] = current_drones + 1

    def reserve_connection(self, from_hub: Hub, to_hub: Hub,
                           turn: int) -> None:
        connection_key = (from_hub, to_hub, turn)
        current_drones = self.conn_load.get(connection_key, 0)

        self.conn_load[connection_key] = current_drones + 1
