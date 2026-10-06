from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from drones import Drone


class HubData(TypedDict):
    type: str
    name: str
    x: int
    y: int
    color: str
    max_drones: int
    zone: str


ConnectionData = TypedDict(
    "ConnectionData",
    {
        "from": str,
        "to": str,
        "max_link_capacity": int,
    },
)


class CleanMap(TypedDict):
    nb_drones: int
    hubs: list[HubData]
    connections: list[ConnectionData]


class Hub:
    def __init__(
                self,
                tipo: str,
                name: str,
                x: int,
                y: int,
                color: str,
                max_drones: int,
                zone: str,
                conn: list[dict[str, int]],
                ):
        self.type = tipo
        self.name = name
        self.coord: tuple[int, int] = (x, y)
        self.color = color
        self.max_drones = max_drones
        self.zone = zone
        self.conn = conn

        self.dr_conn: list[Drone] = []
        self.inside: list[Drone] = []

    def add_conn(self, drone: "Drone", next_hub: "Hub" | None = None) -> int:
        length = len(self.dr_conn)

        if next_hub is None:
            max_link_capacity = sum(capacity for connection in self.conn
                                    for capacity in connection.values())
        else:
            max_link_capacity = next(
                connection[next_hub.name]
                for connection in self.conn
                if next_hub.name in connection
            )
        if length < max_link_capacity:
            self.dr_conn.append(drone)
            return 0
        else:
            return 1

    def del_conn(self, drone: "Drone") -> None:
        if drone in self.dr_conn:
            self.dr_conn.remove(drone)

    def add_inside(self, drone: "Drone") -> int:
        length = len(self.inside)

        if length < self.max_drones:
            self.inside.append(drone)
            return 0
        else:
            return 1

    def del_inside(self, drone: "Drone") -> None:
        if drone in self.inside:
            self.inside.remove(drone)


class Map:
    def __init__(
            self,
            nb_drones: int,
            ):
        self.nb_drones: int = nb_drones
        self.hubs: dict[str, Hub] = {}
        self.start: Hub | None = None
        self.end: Hub | None = None

    def add_hub(self, hub: Hub) -> None:
        if hub.type == "start_hub":
            self.start = hub
        elif hub.type == "end_hub":
            self.end = hub
        self.hubs[hub.name] = hub


def get_class_maps(clean_maps: CleanMap) -> Map:
    new_map = Map(clean_maps["nb_drones"])

    hubs = clean_maps["hubs"]
    cnc = clean_maps["connections"]

    for hub in hubs:
        conn: list[dict[str, int]] = []
        for dct_conn in cnc:
            if dct_conn["from"] == hub["name"]:
                conn.append({dct_conn["to"]: dct_conn["max_link_capacity"]})

        new_hub = Hub(hub["type"],
                      hub["name"],
                      hub["x"],
                      hub["y"],
                      hub["color"],
                      hub["max_drones"],
                      hub["zone"],
                      conn
                      )

        new_map.add_hub(new_hub)
    if new_map.start is None or new_map.end is None:
        raise ValueError("Map must contain a start_hub and an end_hub")

    new_map.start.max_drones = clean_maps["nb_drones"]
    new_map.end.max_drones = clean_maps["nb_drones"]

    return new_map
