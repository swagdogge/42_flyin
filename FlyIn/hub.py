VALID_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


class Hub:
    """represents a Hub in the drone system"""

    def __init__(
            self,
            name: str,
            x: int,
            y: int,
            zone: str = "normal",
            color: str = "none",
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
            info += (" (start)")
        if self.is_end:
            info += (" (end)")
        print(info)
