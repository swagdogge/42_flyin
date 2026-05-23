#!/usr/bin/env python3

from parsing import parse_map
from network import Network
from visualizer import visualize
from drone import Drone
from pathfinder import plan_all_drones


def run_simulation(
    network: Network,
    drones: list[Drone],
    end_hub: str,
) -> list[str]:
    """Run the full simulation and return output lines.

    Args:
        network: The network graph.
        drones: List of all drones, each with a planned timed path.
        end_hub: Name of the destination hub.

    Returns:
        List of strings, one per turn, in the required output format.
    """
    output_lines: list[str] = []
    turn = 0

    while not all(d.delivered for d in drones):
        turn += 1
        turn_moves: list[str] = []

        for drone in drones:
            if drone.delivered:
                continue

            # find what this drone does at this turn
            next_step = None
            for hub_name, arrival_turn in drone.path:
                if arrival_turn == turn:
                    next_step = hub_name
                    break

            if next_step is None:
                # check if drone is mid-transit
                # (arrives next turn to restricted zone)
                prev_hub = None
                next_hub_name = None
                for i, (hub_name, arrival_turn) in enumerate(drone.path):
                    if arrival_turn > turn:
                        next_hub_name = hub_name
                        # find where it came from
                        prev_hub = drone.path[i - 1][0] if i > 0 else None
                        break

                hub = network.get_hub(next_hub_name) if next_hub_name else None
                if (hub and hub.zone == "restricted"
                        and prev_hub and prev_hub != next_hub_name):
                    # check the drone left prev_hub last turn
                    departed = any(
                        h == prev_hub and t == turn - 1
                        for h, t in drone.path
                    )
                    if departed:
                        turn_moves.append(
                            f"{drone.label()}-{prev_hub}-{next_hub_name}"
                        )
                continue

            prev_pos = drone.pos
            drone.pos = next_step

            if next_step == end_hub:
                drone.delivered = True

            next_hub = network.get_hub(next_step)
            # suppress arrival token if we already emitted a transit token
            # last turn for this move (visualizer handles the second half)
            if next_hub.zone == "restricted" and prev_pos != next_step:
                # check if we emitted a transit token last turn
                already_transited = any(
                    h == next_step and t == turn - 1
                    for h, t in drone.path
                ) is False  # path has no entry at turn-1 for this hub
                if already_transited:
                    turn_moves.append(f"{drone.label()}-{next_step}")
            else:
                turn_moves.append(f"{drone.label()}-{next_step}")

        if turn_moves:
            output_lines.append(" ".join(turn_moves))

    return output_lines


def load_map() -> None:
    """
    Asks for a map file
    plans all drone paths
    runs visualizer
    """
    print("""
      ______ _       _____
     |  ____| |     |_   _|
     | |__  | |_   _  | |  _ __
     |  __| | | | | | | | | '_  \\
     | |    | | |_| |_| |_| | | |
     |_|    |_|\\__, |_____|_| |_|
                __/ |
               |___/
    """)
    filename = input("Enter name of file to read map data from: ")

    hubs, connections, nb_drones = parse_map(filename)
    network = Network(hubs, connections)

    start_hub = next(h.name for h in hubs if h.is_start)
    end_hub = next(h.name for h in hubs if h.is_end)

    # Plan collision-free timed paths for all drones at once.
    all_paths = plan_all_drones(network, start_hub, end_hub, nb_drones)

    drones: list[Drone] = []
    for i, path in enumerate(all_paths):
        drone = Drone(id=i + 1, start_hub=start_hub)
        drone.path = path  # list of (hub_name, turn) tuples
        drones.append(drone)

    output_lines = run_simulation(network, drones, end_hub)
    with open("output.txt", "w") as f:
        f.write("\n".join(output_lines))
    print("Launching visualizer...")
    visualize(network, output_lines)


load_map()
