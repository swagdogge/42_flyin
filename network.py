from hub import Hub
from connection import Connection


class Network:
    """represents the full network of hubs and connections
    creates a dictionary with hub names as keys and
    the respective Hub object as value
    """

    def __init__(
            self,
            hublist: list[Hub],
            connections: list[Connection]
            ) -> None:
        self.hubs: dict[str, Hub] = {}
        for hub in hublist:
            self.hubs[hub.name] = hub
        self.connections: list[Connection] = connections
        self.adjacency: dict[str, list[Connection]] = {}
        for hub in hublist:
            self.adjacency[hub.name] = []
        for conn in connections:
            self.adjacency[conn.zone_a].append(conn)
            self.adjacency[conn.zone_b].append(conn)

    def get_hub(self, name: str) -> Hub:
        """return hub object by name"""
        return self.hubs[name]

    def get_neighbours(self, name: str) -> list[tuple[Hub, Connection]]:
        """Return list of (neighbour_hub, connection) pairs for a given hub."""
        result = []
        for conn in self.adjacency[name]:
            if conn.zone_a == name:
                neighbour_name = conn.zone_b
            else:
                neighbour_name = conn.zone_a
            neighbour = self.hubs[neighbour_name]
            if neighbour.zone != "blocked":
                result.append((neighbour, conn))
        return result
