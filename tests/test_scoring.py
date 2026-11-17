"""Tests for the Fly-In scoring and simulation rules."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drones import Drone, get_paths_drones, get_size_paths  # noqa: E402
from fly_in import fly_in  # noqa: E402
from parser.class_maps import Map, get_class_maps  # noqa: E402
from parser.raw_map import syntaxt_parser  # noqa: E402


BENCHMARKS: dict[str, tuple[str, int, int]] = {
    "easy_linear": ("maps/1_easy/01_linear_path.txt", 2, 6),
    "easy_fork": ("maps/1_easy/02_simple_fork.txt", 4, 8),
    "easy_capacity": ("maps/1_easy/03_basic_capacity.txt", 4, 6),
    "medium_dead_end": ("maps/2_medium/01_dead_end_trap.txt", 5, 12),
    "medium_loop": ("maps/2_medium/02_circular_loop.txt", 6, 15),
    "medium_priority": ("maps/2_medium/03_priority_puzzle.txt", 5, 12),
    "hard_maze": ("maps/3_hard/01_maze_nightmare.txt", 8, 30),
    "hard_capacity": ("maps/3_hard/02_capacity_hell.txt", 12, 35),
    "hard_ultimate": ("maps/3_hard/03_ultimate_challenge.txt", 15, 45),
}


def load_level(relative_path: str) -> Map:
    """Parse one map exactly as the application parses a level."""
    path = ROOT / relative_path
    clean_map = syntaxt_parser(path.read_text(encoding="utf-8").splitlines())
    return get_class_maps(clean_map)


def run_level(level: Map) -> tuple[int, list[Drone]]:
    """Run one level and return its number of turns and final drones."""
    if level.start is None:
        raise AssertionError("The test map has no start hub")

    paths = get_paths_drones(level)
    if not paths:
        raise AssertionError("The test map has no valid path")

    drones = [Drone(index, level.start) for index in range(level.nb_drones)]
    for drone in drones:
        drone.paths = paths
        drone.path = paths[0]

    turns = 0
    with contextlib.redirect_stdout(io.StringIO()):
        for _ in fly_in(drones, level, get_size_paths(paths, level)):
            turns += 1
            assert_capacity_constraints(level, drones)

    return turns, drones


def assert_capacity_constraints(level: Map, drones: list[Drone]) -> None:
    """Check occupancy and connection constraints after every simulation turn."""
    for hub in level.hubs.values():
        if len(hub.inside) > hub.max_drones:
            raise AssertionError(
                f"{hub.name} contains {len(hub.inside)} drones; "
                f"capacity is {hub.max_drones}"
            )

        link_capacity = sum(
            capacity for connection in hub.conn
            for capacity in connection.values()
        )
        if len(hub.dr_conn) > link_capacity:
            raise AssertionError(
                f"{hub.name} uses {len(hub.dr_conn)} links; "
                f"capacity is {link_capacity}"
            )

        for drone in hub.inside:
            if drone.current is not hub:
                raise AssertionError(
                    f"{drone.name} is recorded in {hub.name}, "
                    f"but its current hub is {drone.current.name}"
                )


class ScoringSystemTests(unittest.TestCase):
    def test_reference_turn_targets(self) -> None:
        """All mandatory easy, medium and hard targets must be met."""
        failures: list[str] = []
        print()
        print()
        benchmark_paths = {
            relative_path
            for relative_path, _, _ in BENCHMARKS.values()
        }
        discovered_paths = {
            str(path.relative_to(ROOT))
            for difficulty in ("1_easy", "2_medium", "3_hard")
            for path in (ROOT / "maps" / difficulty).glob("*.txt")
        }
        missing_from_benchmark = sorted(discovered_paths - benchmark_paths)
        self.assertFalse(
            missing_from_benchmark,
            "Mappe trovate ma assenti dai benchmark:\n"
            + "\n".join(missing_from_benchmark),
        )

        for name, (path, expected_drones, target) in BENCHMARKS.items():
            with self.subTest(level=name):
                level = load_level(path)
                self.assertEqual(level.nb_drones, expected_drones)
                turns, drones = run_level(level)

                map_path = Path(path)
                level_name = map_path.parent.name
                map_name = map_path.stem
                print(
                    f"Livello: {level_name} | "
                    f"Mappa: {map_name} | "
                    f"Mosse fatte: {turns} | "
                    f"Limite mosse: {target}"
                )

                if turns > target:
                    failures.append(
                        f"{name}: {turns} turns (target <= {target})"
                    )

                self.assertIsNotNone(level.end)
                assert level.end is not None
                self.assertEqual(len(level.end.inside), expected_drones)
                self.assertTrue(all(drone.current is level.end for drone in drones))

        self.assertFalse(
            failures,
            "Scoring targets not met:\n" + "\n".join(failures),
        )

    def test_restricted_zone_costs_two_turns(self) -> None:
        level = load_level("maps/2_medium/02_circular_loop.txt")
        self.assertIsNotNone(level.start)
        assert level.start is not None

        paths = get_paths_drones(level)
        restricted_hub = next(
            hub for path in paths for hub in path if hub.zone == "restricted"
        )
        drone = Drone(0, level.start)

        drone.move(restricted_hub)
        self.assertTrue(drone.flag_conn)
        self.assertIs(drone.current, level.start)

        drone.move(restricted_hub)
        self.assertFalse(drone.flag_conn)
        self.assertIs(drone.current, restricted_hub)

    @unittest.skipUnless(
        os.environ.get("RUN_CHALLENGER") == "1",
        "optional challenger benchmark; run with RUN_CHALLENGER=1",
    )
    def test_optional_challenger_target(self) -> None:
        level = load_level("maps/challenger/01_the_impossible_dream.txt")
        turns, _ = run_level(level)
        print(
            "Livello: challenger | "
            "Mappa: 01_the_impossible_dream | "
            f"Mosse fatte: {turns} | "
            "Limite mosse: 45"
        )
        self.assertLessEqual(turns, 45)


if __name__ == "__main__":
    unittest.main()
