*This project has been created as part of the 42 curriculum by xlopez-g.*

# Fly-in: Autonomous Drone Routing Simulation

## Description
**Fly-in** is an efficient, object-oriented autonomous drone routing engine built in Python 3.10+. The objective of the system is to navigate a fleet of drones from a single origin node (`start_hub`) to a target destination (`end_hub`) through a network of interconnected zones in the minimum possible number of discrete simulation turns.

The simulation strictly enforces complex graph and temporal constraints, including:
- **Zone Occupancy Limits (`max_drones`)**: Restricting how many drones can occupy a zone at any given turn.
- **Connection Capacity (`max_link_capacity`)**: Limiting simultaneous bidirectional traffic across edges.
- **Variable Movement Costs**: Accounting for zone types such as `normal` (1 turn), `restricted` (2 turns), `priority` (preferred 1 turn), and `blocked` (impassable).
- **Conflict & Deadlock Avoidance**: Scheduling movement and strategic waiting turns without collisions.

---

## Technical Choices & Algorithm Design

### Time-Expanded Dijkstra Pathfinding
To route multiple drones through overlapping networks without collisions, the core pathfinding relies on a **Time-Expanded Dijkstra algorithm** coupled with a dynamic **Reservation Table**.

1. **State Representation**: Rather than searching over simple spatial nodes $(u)$, the graph operates over spatio-temporal states $(u, t)$, where $u$ represents a Hub and $t$ represents the discrete simulation turn.
2. **Strategic Waiting**: At any node $u$, a drone has the option to transition to $(u, t+1)$ (staying in place), provided that the node's capacity allows it for that turn.
3. **Priority Weighting**: Priority zones (`priority`) and waiting steps are assigned non-integer fractional heuristics ($0.99$ cost for priority zones, $0.999$ cost for waiting) during search evaluation. This breaks ties in favor of active forward movement through preferred paths while accurately rounding to 1 turn for actual schedule accounting.
4. **Multi-Turn Transit**: Restricted zones (`restricted`) require 2 turns. The algorithm verifies both hub occupancy at $t+2$ and link capacity across both transit turns ($t+1$ and $t+2$).
5. **Reservation Table (`ReservationTable`)**: As each drone plans its path from `D1` to `D_N`, its spatial and edge reservations are written into a global table. Subsequent drones treat reserved slots as occupied, guaranteeing zero capacity conflicts during execution.

---

## Visual Representation Features

The visual output enhances the user experience by delivering real-time simulation tracking directly in the terminal:
- **ANSI Color Coding**: Hub colors defined in map files (e.g., `[color=red]`, `[color=blue]`) dynamically colorize the output terminal text using standard ANSI escape codes.
- **Turn-by-Turn Formatting**: Output step streams display clear drone movements formatted as `D<ID>-<Hub>` or `D<ID>-<FromHub>-<ToHub>` for restricted transit steps.
- **Interactive Step Execution**: Users can step through simulation turns interactively to evaluate state progression during debugging and peer evaluations.

---

## Instructions

### Prerequisites
- Python 3.10 or higher
- `make` utility

### Installation
Set up the virtual environment (`.venv`) and install dependencies (`pydantic`, `flake8`, `mypy`):
```bash
make install
```

### Execution
Run the default simulation:
```bash
make run
```

To specify a custom map file:
```bash
make run MAP=maps/medium_3.map
```

### Debugging
Launch the script in Python's interactive debugger (`pdb`):
```bash
make debug MAP=maps/easy_1.map
```

### Code Quality & Static Analysis
Run static type checks (`mypy`) and style enforcement (`flake8`):
```bash
make lint
```

For strict type checking:
```bash
make lint_strict
```

### Cleaning Artifacts
Remove caches, temporary files, and virtual environments:
```bash
make clean
```

---

## Example Usage

### Input Map File (`example.map`)
```text
nb_drones: 2
start_hub: start 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
connection: start-roof1
connection: start-corridorA
connection: roof1-goal
connection: corridorA-goal [max_link_capacity=1]
```

### Expected Output
```text
D1-corridorA D2-roof1
D1-goal D2-goal
```

---

## Resources

### References & Documentation
- [Python Typing Documentation (`typing` module)](https://docs.python.org/3/library/typing.html)
- [Pydantic V2 Models & Validation](https://docs.pydantic.dev/latest/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [Time-Expanded Graphs for Multi-Agent Pathfinding (MAPF)](https://en.wikipedia.org/wiki/Multi-agent_path_finding)

### AI Usage Declaration
Artificial Intelligence tools (LLMs) were used during this project in accordance with Chapter II instructions:
- **Architecture & Review**: Assisting with PEP 257 docstring formatting, static type hint verifications (`mypy`), and refining `Makefile` rule structures.
- **Verification**: All AI-suggested code snippets were manually reviewed, tested against custom edge-case map files, and validated via `make lint`.