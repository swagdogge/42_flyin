from hub import Hub, VALID_ZONE_TYPES
from connection import Connection


def parse_options(options_str: str, line_num: int) -> dict[str, str]:
    """parse an options block like [zone=type color=color max_drones=int]"""
    options: dict[str, str] = {}
    options_str = options_str.strip("[]").strip()
    for pair in options_str.split():
        if "=" not in pair:
            raise ValueError(f"Line {line_num}: Invalid metadata '{pair}'")
        key, value = pair.split("=", 1)
        options[key] = value
    return options


def _split_options(rest: str, line_num: int) -> tuple[dict[str, str], str]:
    if "[" in rest:
        main, option_str = rest.split("[", 1)
        return parse_options(option_str, line_num), main
    return {}, rest


def _parse_hub(prefix: str, rest: str, line_num: int,
               hub_names: set[str], seen_start: bool,
               seen_end: bool) -> Hub:
    options, main = _split_options(rest, line_num)
    parts = main.strip().split()
    name = parts[0]
    if "-" in name or " " in name:
        raise ValueError(f"Line {line_num}: Hub name '{name}' "
                         "must not contain dashes or spaces")
    try:
        x, y = int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"Line {line_num}: Coordinates must be integers")
    except IndexError:
        raise IndexError(f"Line {line_num}: Index Error!")
    if name in hub_names:
        raise ValueError(f"Line {line_num}: Duplicate hub name '{name}'")
    zone_type = options.get("zone", "normal")
    if zone_type not in VALID_ZONE_TYPES:
        raise ValueError(f"Line {line_num}: Invalid zone type '{zone_type}'")
    try:
        max_drones = int(options.get("max_drones", "1"))
        if max_drones <= 0:
            raise ValueError()
    except ValueError:
        raise ValueError(f"Line {line_num}: "
                         "max_drones must be a positive integer")
    if prefix == "start_hub" and seen_start:
        raise ValueError(f"Line {line_num}: Multiple start_hub defined")
    if prefix == "end_hub" and seen_end:
        raise ValueError(f"Line {line_num}: Multiple end_hub defined")
    return Hub(name=name, x=x, y=y, zone=zone_type,
               color=options.get("color", "none"), max_drones=max_drones,
               is_start=(prefix == "start_hub"), is_end=(prefix == "end_hub"))


def _parse_connection(rest: str, line_num: int,
                      hub_names: set[str],
                      seen_connections: set[frozenset[str]]
                      ) -> Connection | None:
    options, main = _split_options(rest, line_num)
    if "-" not in main:
        raise ValueError(f"Line {line_num}: Connection missing '-' separator")
    a, b = (s.strip() for s in main.split("-", 1))
    if a not in hub_names or b not in hub_names:
        raise ValueError(f"Line {line_num}: Unknown hub, '{a}'")
    pair = frozenset({a, b})
    if pair in seen_connections:
        raise ValueError(f"Line {line_num}: Duplicate connection {a}-{b}")
    seen_connections.add(pair)
    try:
        capacity = int(options.get("max_link_capacity", "1"))
        if capacity <= 0:
            raise ValueError()
    except ValueError:
        raise ValueError(f"Line {line_num}: "
                         "max_link_capacity must be a positive integer")
    return Connection(a, b, capacity)


def parse_map(filename: str) -> tuple[list[Hub], list[Connection], int]:
    """Parse a map config file and return hubs, connections and drone count."""
    hubs: list[Hub] = []
    connections: list[Connection] = []
    nb_drones = 0
    seen_start = seen_end = False
    hub_names: set[str] = set()
    seen_connections: set[frozenset[str]] = set()

    try:
        filename = filename
        open(filename).close()
    except FileNotFoundError:
        filename = filename + ".txt"

    with open(filename) as file:

        for line_num, line in enumerate(file, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"Line {line_num}: Missing colon separator")

            prefix, rest = (s.strip() for s in line.split(":", 1))

            if prefix == "nb_drones":
                try:
                    nb_drones = int(rest)
                    if nb_drones <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"Line {line_num}: "
                                     "nb_drones must be a positive integer")

            elif prefix in ("hub", "start_hub", "end_hub"):
                hub = _parse_hub(
                    prefix, rest, line_num, hub_names, seen_start, seen_end)
                hub_names.add(hub.name)
                seen_start |= hub.is_start
                seen_end |= hub.is_end
                hubs.append(hub)

            elif prefix == "connection":
                conn = _parse_connection(
                    rest, line_num, hub_names, seen_connections)
                if conn:
                    connections.append(conn)

    if not seen_start:
        raise ValueError("No start_hub defined")
    if not seen_end:
        raise ValueError("No end_hub defined")
    if nb_drones == 0:
        raise ValueError("nb_drones not defined or is zero")
    print("File read successfully :D")

    return hubs, connections, nb_drones
