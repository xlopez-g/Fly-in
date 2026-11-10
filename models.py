#!/usr/bin/env python3
"""Models module for the Fly-in drone routing simulation.

This module defines the core data structures, enums, and state management
tables required to model zones (hubs), network connections, drone entities,
and turn-based capacity reservations.

Adheres to PEP 8, PEP 257, and strict mypy type checking standards.
"""

from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class Zone_class(Enum):
    """Enumeration of available zone movement types and costs.

    Attributes:
        NORMAL: Standard movement zone (1 turn cost).
        BLOCKED: Inaccessible zone.
        RESTRICTED: Sensitive zone requiring multi-turn transit (2 turns).
        PRIORITY: Preferred zone for pathfinding algorithms (1 turn cost).
    """

    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class HUB_TYPE(Enum):
    """Enumeration of structural node roles in the map network.

    Attributes:
        START_HUB: Unique simulation origin node.
        HUB: Intermediate navigation node.
        END_HUB: Unique simulation destination node.
    """

    start_hub = "start_hub"
    hub = "hub"
    end_hub = "end_hub"


class Hub(BaseModel):
    """Represents a spatial zone (node) within the routing network.

    Attributes:
        hub_type: Category of the hub (start, regular, or end).
        name: Unique string identifier (no spaces or hyphens).
        x: X-coordinate position on map.
        y: Y-coordinate position on map.
        zone: Operational classification defining traversal cost.
        color: Terminal or visual representation color.
        max_drones: Maximum simultaneous drone capacity.
    """

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
    """Represents a bidirectional edge between two hubs.

    Attributes:
        hub_a: Name of the first connected hub.
        hub_b: Name of the second connected hub.
        max_link_capacity: Maximum simultaneous traversing drones.
    """

    hub_a: str = Field(pattern=r"^[^\s\-]+$")
    hub_b: str = Field(pattern=r"^[^\s\-]+$")
    max_link_capacity: int = Field(default=1, gt=0)


class Drone(BaseModel):
    """Represents an active drone agent in the simulation.

    Attributes:
        id: Unique drone identifier (e.g., 'D1').
        path: List of assigned (Hub, arrival_turn) movement steps.
        path_index: Current step pointer within the assigned path.
    """

    id: str
    path: list[tuple[Hub, int]]
    path_index: int


class Reservation_Table(BaseModel):
    """Tracks time-expanded occupancy for hubs and connections.

    Prevents capacity rule violations and movement conflicts across discrete
    turns during simulation planning.

    Attributes:
        hub_load: Map of (Hub, turn) to current occupying drone count.
        conn_load: Map of (From_Hub, To_Hub, turn) to traversing drone count.
    """

    hub_load: dict[tuple[Hub, int], int] = Field(default_factory=dict)

    conn_load: dict[tuple[Hub, Hub, int], int] = Field(default_factory=dict)

    def is_hub_available(self,
                         hub_name: Hub,
                         turn: int,
                         max_drones: int) -> bool:
        """Check if a hub has remaining capacity at a specific turn.

        Args:
            hub: Target Hub object.
            turn: Simulation turn number.
            max_drones: Maximum allowed occupancy limit for the hub.

        Returns:
            True if current occupancy is strictly less than max_drones.
        """

        current_drones = self.hub_load.get((hub_name, turn), 0)

        if current_drones < max_drones:
            return True

        return False

    def is_connection_available(self,
                                from_hub: Hub,
                                to_hub: Hub,
                                turn: int,
                                max_link_capacity: int) -> bool:
        """Check if a bidirectional connection can accept another drone.

        Args:
            from_hub: Origin Hub object.
            to_hub: Destination Hub object.
            turn: Simulation turn number of traversal.
            max_link_capacity: Maximum allowed capacity for the link.

        Returns:
            True if total bidirectional traffic is below max_link_capacity.
        """

        connection_check = (from_hub, to_hub, turn)
        connection_back = (to_hub, from_hub, turn)

        drones_check = self.conn_load.get(connection_check, 0)
        drones_back = self.conn_load.get(connection_back, 0)

        current_drones = drones_check + drones_back

        if (current_drones < max_link_capacity):
            return True

        return False

    def reserve_hub(self, hub_name: Hub, turn: int) -> None:
        """Reserve a single occupancy slot in a hub for a specific turn.

        Args:
            hub: Target Hub object.
            turn: Simulation turn number.
        """

        hub_key = (hub_name, turn)
        current_drones = self.hub_load.get(hub_key, 0)

        self.hub_load[hub_key] = current_drones + 1

    def reserve_connection(self, from_hub: Hub, to_hub: Hub,
                           turn: int) -> None:
        """Reserve a single traversal slot on a connection for a specific turn.

        Args:
            from_hub: Origin Hub object.
            to_hub: Destination Hub object.
            turn: Simulation turn number of traversal.
        """

        connection_key = (from_hub, to_hub, turn)
        current_drones = self.conn_load.get(connection_key, 0)

        self.conn_load[connection_key] = current_drones + 1
