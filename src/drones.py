from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parser.class_maps import Map, Hub


class Drone:
    def __init__(self, id_drone: int, start: Hub):
        self.id = id_drone
        self.name = "D" + str(id_drone)
        self.path: list[Hub] = []
        self.paths: list[list[Hub]] = []
        self.current = start
        self.flag_conn = False

    def move(self, hub: Hub) -> None:
        if hub.zone == "restricted":
            if self.flag_conn is True:
                self.flag_conn = False
                self.current = hub
            else:
                self.flag_conn = True
        else:
            self.current = hub


def get_paths_drones(level: Map) -> list[list[Hub]]:
    """Return every simple path from the start hub to the end hub."""
    paths: list[list[Hub]] = []

    if level.start is None or level.end is None:
        return paths

    start = level.start
    end = level.end

    def is_blocked(hub: Hub) -> bool:
        return hub.type == "blocked" or hub.zone == "blocked"

    if is_blocked(start) or is_blocked(end):
        return paths

    def find_paths(current: Hub, path: list[Hub], visited: set[str]) -> None:
        if current.name == end.name:
            paths.append(path.copy())
            return

        for connection in current.conn:
            for neighbour_name in connection:
                if (neighbour_name in visited
                        or neighbour_name not in level.hubs):
                    continue

                neighbour = level.hubs[neighbour_name]
                if is_blocked(neighbour):
                    continue

                visited.add(neighbour_name)
                path.append(neighbour)
                find_paths(neighbour, path, visited)
                path.pop()
                visited.remove(neighbour_name)

    find_paths(start, [start], {start.name})
    paths.sort(
        key=lambda path: not any(hub.zone == "priority" for hub in path)
    )
    return paths


def get_size_paths(paths: list[list[Hub]], level: Map) -> list[int]:
    size = []

    for path in paths:
        for hub, next_hub in zip(path, path[1:]):
            tot = []
            link = next(
                connection[next_hub.name]
                for connection in hub.conn
                if next_hub.name in connection
            )
            tot.append(link)
            tot.append(hub.max_drones)
        size.append(min(tot))
    return size
