import pygame as pg
from parser.class_maps import Map
from drones import Drone
from typing import Iterator, List


def render(level: Map, drones: List[Drone],
           movements: Iterator[List[str]]) -> None:
    pg.init()
    width, height = 1200, 500
    surface = pg.display.set_mode((width, height), pg.RESIZABLE)
    clock = pg.time.Clock()
    font = pg.font.SysFont('Arial', 18)
    hub_radius = 22

    coordinates = [hub.coord for hub in level.hubs.values()]
    min_x = min(coord[0] for coord in coordinates)
    max_x = max(coord[0] for coord in coordinates)
    min_y = min(coord[1] for coord in coordinates)
    max_y = max(coord[1] for coord in coordinates)
    margin = 90
    scale: float = 1.0
    origin_x: float = 0.0
    origin_y: float = 0.0

    def update_layout() -> None:
        nonlocal scale, origin_x, origin_y

        window_width, window_height = surface.get_size()
        map_width = max_x - min_x or 1
        map_height = max_y - min_y or 1
        scale = min(
            (window_width - 2 * margin) / map_width,
            (window_height - 2 * margin) / map_height,
        )
        scale = max(scale, 0.1)
        drawn_width = map_width * scale
        drawn_height = map_height * scale
        origin_x = (window_width - drawn_width) / 2
        origin_y = (window_height + drawn_height) / 2

    update_layout()

    def convert(x: int, y: int) -> tuple[int, int]:
        s_x = origin_x + (x - min_x) * scale
        s_y = origin_y - (y - min_y) * scale
        return (round(s_x), round(s_y))

    running = True
    finished = False
    initial_delay = 10_000
    movement_timer = pg.time.get_ticks() + initial_delay
    movement_delay = 500
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.VIDEORESIZE:
                surface = pg.display.set_mode(event.size, pg.RESIZABLE)
                update_layout()

        if not finished and pg.time.get_ticks() >= movement_timer:
            try:
                next(movements)
                movement_timer = pg.time.get_ticks() + movement_delay
            except StopIteration:
                finished = True

        surface.fill("white")

        for hub in level.hubs.values():
            for conn in hub.conn:
                for target_name in conn:
                    target_hub = level.hubs.get(target_name)
                    if target_hub is None:
                        continue

                    pg.draw.line(
                        surface,
                        (70, 70, 70),
                        convert(*hub.coord),
                        convert(*target_hub.coord),
                        6,
                    )

        for hub in level.hubs.values():
            position = convert(*hub.coord)
            color = hub.color if hub.color != "none" else "lightgray"

            pg.draw.circle(surface, color, position, hub_radius)
            pg.draw.circle(surface, "black", position, hub_radius, 2)

            label = font.render(hub.name, True, "black")
            label_rect = label.get_rect(midbottom=(position[0],
                                        position[1] - hub_radius - 6))
            surface.blit(label, label_rect)

        for drone in drones:
            position = convert(*drone.current.coord)
            pg.draw.circle(surface, "black", position, 8)
            label = font.render(drone.name, True, "white")
            surface.blit(label, label.get_rect(center=position))

        pg.display.flip()

        clock.tick(60)

    pg.quit()
