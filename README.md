*This project has been created as part of the 42 curriculum by alcapobi.*

# Fly-In

## Description

Fly-In is a Python simulation of drones travelling through a network of hubs. The
project reads graph-based levels from text files, finds valid routes from a start
hub to an end hub, and simulates several drones moving through the network while
respecting hub and connection capacities.

The project combines graph traversal, scheduling, parsing, and real-time
visualisation. It includes easy, medium, hard, and challenger maps in the
`maps/` directory. Each map can define normal, priority, restricted, or blocked
zones, as well as per-hub and per-connection capacity limits.

## Features

- Text-based map format with validation and useful syntax errors.
- Automatic discovery of maps grouped by difficulty.
- Multiple simple paths from the start hub to the end hub.
- Priority-aware route selection.
- Hub capacity and connection capacity handling.
- Restricted zones that require two simulation turns to cross.
- Interactive Pygame visualisation with automatic resizing.
- Easy-to-hard sample maps for functional and stress testing.

## Algorithm and Implementation Strategy

### 1. Parsing and graph construction

The parser in `src/parser/raw_map.py` reads each map line by line. Regular
expressions validate the declarations for the number of drones, hubs, and
connections. Optional metadata defines a hub's zone, colour, maximum number of
drones, or a connection's maximum link capacity.

After syntax and consistency checks, `src/parser/class_maps.py` converts the
parsed dictionaries into `Map` and `Hub` objects. Connections are stored as an
adjacency list, which keeps graph traversal simple and makes capacity checks
local to the relevant hub or link.

### 2. Path discovery

`get_paths_drones()` in `src/drones.py` uses depth-first search to enumerate all
simple paths between the start and end hubs. A `visited` set prevents cycles from
being followed indefinitely. Blocked hubs are ignored. The resulting paths are
ordered so that paths containing a priority zone are considered first.

### 3. Drone scheduling

The `fly_in()` generator in `src/fly_in.py` advances the simulation one turn at
a time:

1. Each drone selects its next hub from its available paths.
2. A priority-containing remaining path is preferred, then the shorter path.
3. The current hub checks whether the outgoing connection has free capacity.
4. The destination hub checks whether it has room for another drone.
5. Restricted hubs consume a first turn to enter and a second turn to complete
	 the move.
6. Successful movements are yielded and printed as `D<id>-<hub>` entries.

The simulation stops when every drone is inside the end hub. If no drone can
make progress, it raises an error instead of looping forever.

## Visual Representation

The Pygame renderer in `src/render.py` displays the map as an interactive graph:

- Hubs are coloured circles according to their map metadata.
- Connections are drawn as dark lines between hubs.
- Hub names are displayed above their circles.
- Drones appear as black markers labelled with their identifiers.
- The graph is scaled and centred whenever the window is resized.
- Movements are animated every 500 ms after a short initial pause, making
	capacity queues and restricted-zone delays visible.

This visual feedback makes the scheduling strategy easier to inspect than a
text-only trace: users can see congestion, route convergence, and the gradual
arrival of drones at the destination while the simulation is running.

## Instructions

### Requirements

- Python 3.14 or newer.
- `uv` for dependency management.
- A graphical environment supported by Pygame.

### Installation

From the repository root:

```bash
uv sync
```

This installs the dependencies declared in `pyproject.toml`, including Pygame,
Flake8, and mypy.

### Execution

The program is interactive. It first asks for a difficulty and then for a map:

```bash
cd src
python __main__.py
```

Alternatively, use the provided Makefile:

```bash
cd src
make install
make run
```

Choose a difficulty and level from the numbered menus. A Pygame window then
shows the selected simulation. Close the window to exit.

### Validation

The project provides lint and type-check commands:

```bash
cd src
make lint
make lint-strict
```

The parser automatically loads every map under `maps/`, so malformed map files
are reported when the program starts.

## Map Format

A minimal map contains a drone count, a start hub, an end hub, and connections:

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Supported hub zones are `normal`, `priority`, `restricted`, and `blocked`.
Metadata can also set `max_drones`; connections can set
`max_link_capacity`.

## Example

For the minimal map above, the two drones share links with the default capacity
of one. A representative simulation output is:

```text
D0-waypoint1
D0-waypoint2 D1-waypoint1
D0-goal D1-waypoint2
D1-goal
```

The second drone waits whenever the first drone occupies the only available
link or destination slot, demonstrating the capacity rules.

## Project Structure

```text
src/
├── __main__.py              # CLI menus and application entry point
├── drones.py                # Drone model and path discovery
├── fly_in.py                # Turn-by-turn simulation
├── render.py                # Pygame visualisation
└── parser/
		├── raw_map.py           # Text parsing and validation
		└── class_maps.py        # Map and hub domain objects
maps/                        # Sample levels grouped by difficulty
```

## Resources

- [Python documentation](https://docs.python.org/3/) - language reference and
	standard library documentation.
- [Python `re` documentation](https://docs.python.org/3/library/re.html) -
	regular expressions used by the map parser.
- [Python graphlib documentation](https://docs.python.org/3/library/graphlib.html)
	- standard-library graph concepts and terminology.
- [Pygame documentation](https://www.pygame.org/docs/) - window management,
	drawing, event handling, and timing used by the renderer.
- [Depth-first search](https://en.wikipedia.org/wiki/Depth-first_search) -
	reference for the path enumeration strategy.
- [Graph theory](https://en.wikipedia.org/wiki/Graph_theory) - background for
	modelling hubs and connections as a graph.

### Use of AI

AI assistance was used during development to help structure and review parts of
the project, including:

- discussing the decomposition of the application into parsing, graph, domain,
	simulation, and rendering modules;
- reviewing edge cases involving cycles, blocked hubs, capacity limits, and
	restricted-zone movement;
- drafting and editing this README, including its usage examples and resource
	list.

The final implementation, design decisions, testing, and verification remain
the responsibility of the project author.
<>