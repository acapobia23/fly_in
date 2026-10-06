from parser import get_raw_levels, get_clean_maps
from parser.class_maps import Map
import os
import pygame as pg
from fly_in import fly_in
from render import render
from drones import Drone, get_paths_drones, get_size_paths
from typing import TypeAlias


Maps: TypeAlias = dict[str, dict[str, Map]]


def choose_level(data: Maps) -> Map:
    key_diff: list[str] = list(data)
    print(key_diff)
    difficulty: int = -1
    key_list: list[str] = []

    while difficulty == -1:
        try:
            print("Choose Difficulty:")
            for line, key in enumerate(key_diff):
                print(f"{line}.", key)
                key_list.append(key)
            print(f"{line + 1}. exit")

            choose = int(input(":"))

            if choose == (line + 1):
                exit()

            if choose > line:
                print("Wrong, retry.")
                os.system('clear')
                continue
            difficulty = choose

        except ValueError:
            os.system('clear')
            continue

    os.system('clear')
    print(difficulty)

    diff = key_list[difficulty]
    levels: dict[str, Map] = data[diff]

    level = -1
    key_lvl: list[str] = []

    while level == -1:
        try:
            print("choose Level:")
            for line, key in enumerate(levels):
                print(f"{line}.", key)
                key_lvl.append(key)
            print(f"{line + 1}. exit")

            choose = int(input(":"))

            if choose == (line + 1):
                exit()

            if choose > line:
                print("Wrong, retry.")
                os.system('clear')
                continue
            level = choose

        except ValueError:
            os.system('clear')
            continue

    os.system('clear')
    return levels[key_lvl[level]]


def maps_parser() -> Maps:

    clean_maps: Maps = {}

    raw_maps = get_raw_levels()
    if not raw_maps:
        return clean_maps

    clean_maps = get_clean_maps(raw_maps)

    if not clean_maps:
        return {}

    return clean_maps


def main() -> None:

    data: Maps = maps_parser()

    if not data:
        print("data None:", data)
        return

    level: Map = choose_level(data)

    if level.start is None:
        raise ValueError("Map must contain a start_hub")

    start = level.start

    paths = get_paths_drones(level)

    size_paths = get_size_paths(paths, level)

    drones = []
    for i in range(level.nb_drones):
        tmp = Drone(i, start)
        tmp.paths = paths
        tmp.path = paths[0]
        drones.append(tmp)

    movements = fly_in(drones, level, size_paths)
    render(level, drones, movements)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pg.quit()
