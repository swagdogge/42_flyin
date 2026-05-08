from network import Network
def dijkstra(network: Network, start: str, end: str) -> list[str]:
    """Find lowest cost path from start to end using Dijkstra algorythm"""
    costs: dict[str, float] = {name: float("inf") for name in network.hubs}
    costs[start] = 0
    
    return path