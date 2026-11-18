*This activity has been created as part of the 42 curriculum by klafi*

# Fly-In

## Description

Fly-In simulates a fleet of drones moving through a network of connected zones.
The goal is to route every drone from the start hub to the end hub while
accounting for zone types, zone capacity, connection capacity, and restricted
zones that take two turns to cross. The project parses a text map, plans and
records drone movements, and displays the simulation in a graphical window.

## Instructions

### Requirements

- Python 3.14 or later (as declared in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/)
- A graphical desktop session for the Pygame visualization

### Install

From the repository root, install the project and its dependencies:

```bash
make install
```

This runs `uv sync`.

### Run

Pass a map file and a path for the movement output:

```bash
uv run python src/__main__.py maps/easy/01_linear_path.txt moves.txt
```

The program writes the turn-by-turn moves to `moves.txt` and opens the
visualization. Close the window or press `4` to exit it.

The Makefile defines `make run` for the configured challenge map, `make debug`
for the Python debugger, `make lint` for flake8 and mypy, and `make clean` to
remove Python and mypy caches. The current `run` and `debug` targets need
correction; see [known requirements gaps](#known-requirements-gaps).

### Map format

A map begins with the number of drones, followed by start/end hubs, regular
hubs, and connections. Zone metadata can set `zone`, `color`, and
`max_drones`; connection metadata can set `max_link_capacity`.

```text
nb_drones: 1
start_hub: start 0 0
hub: middle 1 0
end_hub: goal 2 0
connection: start-middle
connection: middle-goal
```

For this input, the expected movement output is:

```text
D1-middle
D1-goal
```

Each output line represents a turn. Moves on the same line are separated by
spaces; drones that do not move are omitted.

## Algorithm and implementation

The map parser validates zone and connection declarations and builds a
`Network` of `Zone`, `Connection`, and `Drone` objects. Pydantic models enforce
field constraints and validate that the start and end hubs are connected.

The network calculates zone distances from the destination with Dijkstra's
algorithm. It uses uniform-cost search to check reachability and A* path-cost
estimates when choosing a next zone for each drone. Zone type costs contribute
to path selection, the routing logic has a preference rule for priority zones,
and per-turn path caching avoids repeating some searches. A turn records the
selected drone moves and updates zone and connection occupancy.

## Visualization

The Pygame window displays the map background, zone sprites and labels,
connections, animated drone sprites, and a turn counter. Recognized zone color
names are applied to the zone graphics. The animation shows the recorded route
turn by turn, making drone progress and the map layout easier to follow.


## Resources

- [Dijkstra's algorithm — video](https://youtu.be/j0OUwduDOS0)
- [Uniform-cost search and A* — video](https://youtu.be/88I6IidylGc)
- [Python documentation](https://docs.python.org/3/)
- [Pygame documentation](https://www.pygame.org/docs/)
- [Pydantic documentation](https://docs.pydantic.dev/)

### Use of AI

AI assistance was used to add and check Python docstrings, compare the project
with the subject's requirements, and revise this README. The pathfinding and
simulation implementation is documented above; AI-generated changes should be
reviewed and understood as part of the project.
