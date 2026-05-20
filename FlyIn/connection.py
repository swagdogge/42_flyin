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

    def get_info(self):
        print(f"Connection {self.zone_a}-{self.zone_b}, "
              f"capacity: {self.max_link_capacity}")
