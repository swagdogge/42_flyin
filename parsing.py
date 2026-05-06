import pygame

VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}

class Hub:
    """represents a Hub in the drone system"""

    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone: str = "normal",
            color: str= "none",
            max_drones: int = 1,
            is_start: bool = False,
            is_end: bool = False,
        ) -> None:
            """Initialize Hub instance"""
            self.name = name
            self.x = x
            self.y = y
            self.zone = zone
            self.color = color
            self.max_drones = max_drones
            self.is_start = is_start
            self.is_end = is_end
    
    def get_info(self):
         info = (f"Hub {self.name}: {self.x}, {self.y}")
         if self.is_start:
            info +=(" (start)")
         if self.is_end:
            info +=(" (end)")
         print(info)

class Connection:
    """represents a connection between two hubs"""

    def __init__(
        self, 
        zone_a: str,
        zone_b: str,
        max_link_capacity: int = 1,
    ) -> None:
        """initialize a Connection instance"""
        self.zone_a = zone_a
        self.zone_b = zone_b
        self.max_link_capacity = max_link_capacity


def parse_options(options_str: str, line_num:int) -> dict:
    """parse an options block like [zone=type color=color max_drones=int]"""
    options: dict[str, str] = {}
    options_str = options_str.strip("[]").strip()
    for pair in options_str.split():
        if "=" not in pair:
            raise ValueError(f"Line {line_num}: Invalid metadata 'pair'")
        key, value = pair.split("=", 1)
        options[key] = value
    return options


def parse_map(filename: str) -> tuple[list[Hub], list[Connection], int]:
    """parse a map config file and return hubs, connections and drone count"""
    hubs: list[Hub] = []
    connections: list[Connection] = []
    nb_drones: int = 0
    seen_start = False
    seen_end = True
    hub_names: set[str] = set()
    seen_connections:set[frozenset[str]] = set()
    with open(filename, "r") as file:
        for line_num, line in enumerate(file, start = 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                raise ValueError(f"Line {line_num}: Missing colon separator")
            prefix, rest = line.split(":", 1)
            prefix = prefix.strip()
            rest = rest.strip()
            if prefix == "nb_drones":
                try:
                    nb_drones = int(rest)
                    if nb_drones <= 0:
                        raise ValueError()
                except:
                    raise ValueError(f"Line {line_num}: nb_drones must be a positive integer")

            elif prefix in ("hub", "start_hub", "end_hub"):
                options: dict[str, str] = {}
                if "[" in rest:
                    main, option_str = rest.split("[", 1)
                    options = parse_options(option_str, line_num)
                else:
                    main = rest

                parts = main.strip().split()
                name = parts[0]
                try:
                    x = int(parts[1])
                    y = int(parts[2])
                except:
                    raise ValueError(f"Line {line_num}: Coordinates must be integers")
                
                if name in hub_names:
                    raise ValueError(f"Line {line_mum}: Duplicate hub name '{name}'")
                hub_names.add(name)

                zone_type = options.get("zone", "normal")
                if zone_type not in VALID_ZONE_TYPES:
                    raise ValueError(
                        f"Line {line_num}: Invalid zone type 'zone_type'"
                    )
                
                try:
                    max_drones = int(options.get("max_drones", "1"))
                    if max_drones <= 0:
                        raise ValueError()
                except ValueError:
                    raise ValueError(
                        f"Line {line_num}: max_drones must be a positive integer"
                    )

                if prefix == "start_hub":
                    if seen_start:
                        raise ValueError(f"Line {line_num}: Multiple start_hub defined")
                    seen_start = True
                if prefix == "end_hub":
                    if seen_end:
                        raise ValueError(f"Line {line_num}: Multiple end_hub defined")
                    seen_end = True


                hubs.append(Hub(
                    name=name, x=x, y=y,
                    zone=zone_type,
                    color=options.get("color", "none"),
                    max_drones=max_drones,
                    is_start=(prefix == "start_hub"),
                    is_end=(prefix == "end_hub"),
                ))
            elif prefix == "connection":
                    options = {}
                    if "[" in rest:
                        main, option_str = rest.split("[", 1)
                        options = parse_options(option_str, line_num)
                    else:
                        main = rest

                    if "-" not in main:
                        raise ValueError(f"Line {line_num}: Connection missing '-' separator")

                    a, b = main.strip().split("-", 1)
                    a, b = a.strip(), b.strip()

                    if a not in hub_names or b not in hub_names:
                        raise ValueError(
                            f"Line {line_num}: Connection references unknown hub(s)"
                        )

                    pair = frozenset({a, b})
                    if pair in seen_connections:
                        raise ValueError(f"Line {line_num}: Duplicate connection {a}-{b}")
                    seen_connections.add(pair)

                    try:
                        capacity = int(options.get("max_link_capacity", "1"))
                        if capacity <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ValueError(
                            f"Line {line_num}: max_link_capacity must be a positive integer"
                        )

                    connections.append(Connection(a, b, capacity))

        if not seen_start:
            raise ValueError("No start_hub defined")
        if not seen_end:
            raise ValueError("No end_hub defined")
        if nb_drones == 0:
            raise ValueError("nb_drones not defined or is zero")

    return hubs, connections, nb_drones






filename = input("Enter name of file to read data from: ")
