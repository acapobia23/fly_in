from pathlib import Path
import re
from typing import TypedDict

from .class_maps import CleanMap, ConnectionData, HubData, Map, get_class_maps

# zone|color|max_drones|max_link_capacity

DRONE_RE = re.compile(r"^nb_drones:\s*(?P<nb_drones>\d+)\s*$")

HUB_RE = re.compile(
            r"^(?P<type>start_hub|end_hub|hub):\s+"
            r"(?P<name>[A-Za-z0-9_]+)\s+"
            r"(?P<x>-?\d+)\s+"
            r"(?P<y>-?\d+)"
            r"(?:\s+\[(?P<metadata>.*?)\])?\s*$"
        )

CONNECTION_RE = re.compile(
            r"^connection:\s+"
            r"(?P<from>[A-Za-z0-9_]+)-(?P<to>[A-Za-z0-9_]+)"
            r"(?:\s+\[(?P<metadata>.*?)\])?\s*$"
        )

METADATA_RE = re.compile(
            r"(?P<key>\w+)=(?P<value>[A-Za-z0-9_]+)"
        )

METADATA_KEYS = {
            "zone",
            "color",
            "max_drones",
            "max_link_capacity",
        }


ZONES_VALID = {
            "normal",
            "blocked",
            "restricted",
            "priority",
        }


class ParsedMap(TypedDict):
    nb_drones: int | None
    hubs: list[HubData]
    connections: list[ConnectionData]


def syntaxt_parser(level: list[str]) -> CleanMap:
    clean_map: ParsedMap = {
        "nb_drones": None,
        "hubs": [],
        "connections": [],
    }

    for n_line, raw_line in enumerate(level, 1):
        line = raw_line.strip()
        c_ash = 0

        if not line or line.startswith("#"):
            c_ash += 1
            continue

        m = DRONE_RE.fullmatch(line)

        if m:
            if (c_ash - n_line) > 2:
                raise ValueError("nb_drones not at start", n_line)

            if clean_map["nb_drones"] is not None:
                raise ValueError(
                        f"Multiple nb_drones lines Error:"
                        f"riga: {n_line} : {line}")

            clean_map["nb_drones"] = int(m.group("nb_drones"))
            continue

        m = HUB_RE.fullmatch(line)

        if m:
            raw_metadata = m.group("metadata")
            metadata: dict[str, str] = {}

            if raw_metadata:
                raw_metadata = raw_metadata.split()

                for raw_data in raw_metadata:
                    valid = METADATA_RE.fullmatch(raw_data)

                    if not valid:
                        raise ValueError(
                                    f"Metadata Error key: {raw_data}"
                                    f"  on line: {n_line}, line({line})"
                                )

                    key = valid.group("key")
                    value = valid.group("value")

                    if key not in METADATA_KEYS:
                        raise ValueError(
                                    f"m_data Not Define Error key:{key}"
                                    f"  on line: {n_line}, line({line})"
                                )

                    if key in metadata:
                        raise ValueError(
                                f"Multiple key define, key {key}"
                                f"riga:\n   {n_line}: {line}"
                            )

                    if key == "zone":
                        if value not in ZONES_VALID:
                            raise ValueError(
                                        f"Zone Error value:{value}"
                                        f"  on line: {n_line}, line({line})"
                                    )
                    metadata[key] = value

            hub: HubData = {
                "type": m.group("type"),
                "name": m.group("name"),
                "x": int(m.group("x")),
                "y": int(m.group("y")),
                "zone": metadata.get("zone", "normal"),
                "color": metadata.get("color", "none"),
                "max_drones": int(metadata.get("max_drones", "1")),
            }

            clean_map["hubs"].append(hub)

            continue

        m = CONNECTION_RE.fullmatch(line)

        if m:
            raw_metadata = m.group("metadata")
            max_link_capacity = 1

            if raw_metadata:
                meta_cn = METADATA_RE.fullmatch(raw_metadata)

                if not meta_cn:
                    raise ValueError(
                            f"Not Valid metadata Syntax"
                            f"riga:\n   {n_line}: {line}"
                        )

                key = meta_cn.group("key")
                value = meta_cn.group("value")

                if key != "max_link_capacity":
                    raise ValueError(
                                f"Metadata Connections Error key:"
                                f"{key} on line:"
                                f"  {n_line}: {line}"
                            )

                max_link_capacity = int(value)
                if max_link_capacity < 1:
                    raise ValueError("max_link_capacity Error")

            connection: ConnectionData = {
                "from": m.group("from"),
                "to": m.group("to"),
                "max_link_capacity": max_link_capacity,
            }
            clean_map["connections"].append(connection)
            continue

        raise ValueError(
                        "Syntax Error on line:"
                        f"  {n_line}: {line}"
                    )

    if clean_map["nb_drones"] is None:
        raise ValueError("Missing nb_drones")

    check_clean_map(clean_map)

    return {
        "nb_drones": clean_map["nb_drones"],
        "hubs": clean_map["hubs"],
        "connections": clean_map["connections"],
    }


def check_clean_map(clean_map: ParsedMap) -> None:

    hubs = clean_map["hubs"]

    names: list[str] = []
    hub_types: list[str] = []

    for hub in hubs:
        if hub["type"] == "start_hub" and hub["type"] in hub_types:
            raise ValueError("Duplicate Start_Hub")
        if hub["type"] == "end_hub" and hub["type"] in hub_types:
            raise ValueError("Duplicate end_hub")
        if hub["name"] in names:
            raise ValueError("duplicate name hub")

        hub_types.append(hub["type"])
        names.append(hub["name"])

    if not hub_types or hub_types[-1] != "end_hub":
        raise ValueError("end_hub Error")

    if hub_types[0] != "start_hub":
        raise ValueError("start_hub Error")

    seen_conn = set()

    for connections in clean_map["connections"]:
        start = connections["from"]
        end = connections["to"]

        normalized = frozenset((start, end))

        if normalized in seen_conn:
            raise ValueError("Duplicate Connections:", start, end)

        seen_conn.add(normalized)

    return


def get_clean_maps(
    raw_maps: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, Map]]:

    clean_maps: dict[str, dict[str, Map]] = {}

    try:
        for lvl_name, lvl_maps in raw_maps.items():
            clean_maps[lvl_name] = {}

            for lvl in lvl_maps:
                tmp = syntaxt_parser(lvl_maps[lvl])

                clean_maps[lvl_name][lvl] = get_class_maps(tmp)

    except ValueError as e:
        print(f"Parsing Error on file {lvl}:")
        print(e)
        return {}

    return clean_maps


def get_raw_levels() -> dict[str, dict[str, list[str]]]:

    try:
        path = (Path(__file__).parent / "../../maps").resolve()

        levels: dict[str, dict[str, list[str]]] = {}

        if not path.is_dir():
            raise FileNotFoundError(f"Cartella maps non esiste: {path}")

        for level in path.iterdir():
            if level.is_dir():
                levels[level.name] = {}

                for file in level.iterdir():
                    if file.is_file():
                        with file.open("r", encoding="utf-8") as f:
                            raws = [raw.rstrip("\n") for raw in f]

                        levels[level.name][file.stem] = raws

        return levels

    except FileNotFoundError as e:
        print(f"Errore: {e}")
        return {}

    except OSError as e:
        print(f"Errore durante la lettura dei file: {e}")
        return {}

    except Exception as e:
        print(f"Errore imprevisto: {e}")
        return {}
