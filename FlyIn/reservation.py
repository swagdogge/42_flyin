class ReservationTable:
    """Tracks hub and link usage across simulation turns."""

    def __init__(self) -> None:
        """Initialize empty reservation table."""
        self.hub_usage: dict[int, dict[str, int]] = {}
        self.link_usage: dict[int, dict[tuple[str, str], int]] = {}

    @staticmethod
    def edge_key(a: str, b: str) -> tuple[str, str]:
        """Return a normalised, order-independent key for an edge."""
        if a < b:
            return (a, b)
        return (b, a)

    def reserve_hub(self, hub_name: str, turn: int) -> None:
        """Record one drone occupying hub_name at turn."""
        if turn not in self.hub_usage:
            self.hub_usage[turn] = {}
        self.hub_usage[turn][hub_name] = (
            self.hub_usage[turn].get(hub_name, 0) + 1
        )

    def reserve_link(self, a: str, b: str, turn: int) -> None:
        """Record one drone traversing the edge (a, b) at turn."""
        key = self.edge_key(a, b)
        if turn not in self.link_usage:
            self.link_usage[turn] = {}
        self.link_usage[turn][key] = (
            self.link_usage[turn].get(key, 0) + 1
        )

    def hub_used(self, hub_name: str, turn: int) -> int:
        """Return how many drones occupy hub_name at turn."""
        return self.hub_usage.get(turn, {}).get(hub_name, 0)

    def link_used(self, a: str, b: str, turn: int) -> int:
        """Return how many drones traverse edge (a, b) at turn."""
        key = self.edge_key(a, b)
        return self.link_usage.get(turn, {}).get(key, 0)