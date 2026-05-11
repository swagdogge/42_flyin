class Drone:
    """Represents a drone navigating between hubs in the simulation."""

    def __init__(self, id: int, start_hub: str) -> None:
        """Initialize a drone at the start hub.

        Args:
            id: Unique numeric identifier for this drone.
            start_hub: Name of the hub the drone starts at.
        """
        self.id: int = id
        self.pos: str = start_hub          # current hub name
        self.path: list[tuple[str, int]] = []          # planned path (list of hub names)
        self.path_index: int = 0           # where in the path we currently are
        self.delivered: bool = False       # True once it reaches end_hub
        self.turns_in_transit: int = 0     # countdown for restricted zone (2-turn move)
        self.next_pos: str | None = None   # destination of current in-transit move
        self.waiting: bool = False         # True if drone is holding position this turn

    def is_in_transit(self) -> bool:
        """Return True if the drone is mid-flight toward a restricted zone."""
        return self.turns_in_transit > 0

    def label(self) -> str:
        """Return the output label for this drone, e.g. D1."""
        return f"D{self.id}"
    
    def start_transit(self, destination: str) -> None:
        """Begin a 2-turn move toward a restricted zone.
        
        Args:
            destination: Name of the hub the drone is heading to.
        """
        self.turns_in_transit = 1
        self.next_pos = destination