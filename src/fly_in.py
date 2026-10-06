from parser.class_maps import Hub, Map
from drones import Drone
from typing import Iterator, List


def _next_hub(drone: Drone) -> Hub | None:
    paths = drone.paths or [drone.path]
    candidates = []

    for path in paths:
        if drone.current not in path:
            continue

        current_index = path.index(drone.current)
        if current_index + 1 == len(path):
            continue

        remaining_path = path[current_index + 1:]
        is_priority = any(hub.zone == "priority" for hub in remaining_path)
        candidates.append(
            (not is_priority, len(path), path[current_index + 1])
        )

    if not candidates:
        return None

    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
    return candidates[0][2]


def fly_in(
    drones: List[Drone], level: Map, size_paths: List[int]
) -> Iterator[List[str]]:
    if level.start is None or level.end is None:
        raise ValueError("Map must contain a start_hub and an end_hub")

    start = level.start
    end = level.end

    for drone in drones:
        start.add_inside(drone)

    while len(end.inside) != level.nb_drones:
        moves = []
        progressed = False

        for hub in level.hubs.values():
            hub.dr_conn.clear()

        for drone in drones:
            if drone.current is end:
                continue

            next_hub = _next_hub(drone)
            if next_hub is None:
                continue

            if drone.current.add_conn(drone, next_hub) != 0:
                continue

            if next_hub.zone == "restricted" and drone.flag_conn is False:
                drone.flag_conn = True
                progressed = True
                continue

            if next_hub.add_inside(drone) != 0:
                drone.current.del_conn(drone)
                continue

            drone.current.del_inside(drone)
            drone.move(next_hub)
            progressed = True
            if drone.flag_conn is False:
                moves.append(f"{drone.name}-{next_hub.name}")

        if not progressed:
            raise RuntimeError("No Drone can move: check capacity and roads")

        if moves:
            print(" ".join(moves))
        yield moves
