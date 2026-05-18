from network import Network
from reservation import ReservationTable


MAX_TIME = 200


def movement_cost(zone_type: str) -> int:
    """Return the turn cost to enter a zone of the given type."""
    if zone_type == "restricted":
        return 2
    return 1


def can_wait(
    network: Network,
    reservations: ReservationTable,
    hub_name: str,
    turn: int,
) -> bool:
    """Return True if a drone may stay at hub_name through turn."""
    hub = network.hubs[hub_name]
    if hub.is_start or hub.is_end:
        return True
    return reservations.hub_used(hub_name, turn) < hub.max_drones


def can_traverse(
    network: Network,
    reservations: ReservationTable,
    current: str,
    neighbor_name: str,
    arrival_turn: int,
    current_turn: int,
    connection_capacity: int,
) -> bool:
    """Return True if moving from current to neighbor_name is valid."""
    neighbor = network.hubs[neighbor_name]
    move_cost = movement_cost(neighbor.zone)
    edge = ReservationTable.edge_key(current, neighbor_name)

    for t in range(current_turn, current_turn + move_cost):
        if reservations.link_used(edge[0], edge[1], t) >= connection_capacity:
            return False

    if not neighbor.is_start and not neighbor.is_end:
        if reservations.hub_used(neighbor_name, arrival_turn) >= neighbor.max_drones:
            return False

    return True


def reconstruct_path(
    previous: dict[tuple[str, int], tuple[str, int] | None],
    end_state: tuple[str, int],
) -> list[tuple[str, int]]:
    """Walk back through previous to build the timed path."""
    path: list[tuple[str, int]] = []
    current: tuple[str, int] | None = end_state
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path


def timed_astar(
    network: Network,
    reservations: ReservationTable,
    start: str,
    end: str,
) -> list[tuple[str, int]]:
    """
    Find the lowest-turn timed path from start to end.

    Uses a simple priority queue (plain list + min-pop) so no imports
    are needed.  Priority zones are preferred by a small tie-break bonus.

    Args:
        network: The full hub/connection graph.
        reservations: Current reservation state (read-only here).
        start: Name of the starting hub.
        end: Name of the destination hub.

    Returns:
        A list of (hub_name, turn) pairs, or [] if no path exists.
    """
    # Each entry: (arrival_turn, priority_bonus, hub_name)
    # priority_bonus is 0 for priority zones, 1 otherwise — lower is better.
    start_state: tuple[str, int] = (start, 0)

    queue: list[tuple[int, int, str]] = [(0, 0, start)]
    costs: dict[tuple[str, int], int] = {start_state: 0}
    previous: dict[tuple[str, int], tuple[str, int] | None] = {
        start_state: None
    }
    visited: set[tuple[str, int]] = set()

    while queue:
        # Pop the entry with the smallest (arrival_turn, priority_bonus).
        min_index = 0
        for i in range(1, len(queue)):
            if queue[i] < queue[min_index]:
                min_index = i
        cost, _, current = queue.pop(min_index)
        current_turn = cost

        state: tuple[str, int] = (current, current_turn)
        if state in visited:
            continue
        visited.add(state)

        if current == end:
            return reconstruct_path(previous, state)

        if current_turn >= MAX_TIME:
            continue

        # --- WAIT ---
        wait_turn = current_turn + 1
        wait_state: tuple[str, int] = (current, wait_turn)
        if wait_state not in visited and can_wait(
            network, reservations, current, wait_turn
        ):
            old = costs.get(wait_state, MAX_TIME + 1)
            if wait_turn < old:
                costs[wait_state] = wait_turn
                previous[wait_state] = state
                bonus = 0 if network.hubs[current].zone == "priority" else 1
                queue.append((wait_turn, bonus, current))

        # --- MOVE ---
        for neighbor, connection in network.get_neighbours(current):
            if neighbor.zone == "blocked":
                continue

            move_cost = movement_cost(neighbor.zone)
            arrival_turn = current_turn + move_cost
            new_state: tuple[str, int] = (neighbor.name, arrival_turn)

            if new_state in visited:
                continue

            if not can_traverse(
                network, reservations,
                current, neighbor.name,
                arrival_turn, current_turn,
                connection.max_link_capacity,
            ):
                continue

            if arrival_turn < costs.get(new_state, MAX_TIME + 1):
                costs[new_state] = arrival_turn
                previous[new_state] = state
                bonus = 0 if neighbor.zone == "priority" else 1
                queue.append((arrival_turn, bonus, neighbor.name))

    return []


def commit_path(
    reservations: ReservationTable,
    path: list[tuple[str, int]],
) -> None:
    """Write a planned path into the reservation table."""
    for i, (hub_name, turn) in enumerate(path):
        reservations.reserve_hub(hub_name, turn)
        if i + 1 < len(path):
            next_hub, next_turn = path[i + 1]
            if next_hub != hub_name:
                # reserve all link turns during transit
                for t in range(turn, next_turn):
                    reservations.reserve_link(hub_name, next_hub, t)
            else:
                # drone is waiting — reserve every turn it sits here
                for t in range(turn + 1, next_turn):
                    reservations.reserve_hub(hub_name, t)


def plan_all_drones(
    network: Network,
    start: str,
    end: str,
    nb_drones: int,
) -> list[list[tuple[str, int]]]:
    """
    Plan collision-free paths for all drones using cooperative pathfinding.

    Each drone is planned in order.  Once planned, its path is committed
    to the shared reservation table so later drones route around it.

    Args:
        network: The hub/connection graph.
        start: Start hub name.
        end: End hub name.
        nb_drones: How many drones to route.

    Returns:
        A list of timed paths, one per drone.
    """
    reservations = ReservationTable()
    all_paths: list[list[tuple[str, int]]] = []

    for i in range(nb_drones):
        path = timed_astar(network, reservations, start, end)
        if not path:
            # No path found for this drone — return what we have so far.
            break
        commit_path(reservations, path)
        print(f"path committed for drone {i}")
        all_paths.append(path)

    return all_paths