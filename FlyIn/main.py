from parsing import parse_map
from hub import Hub
from connection import Connection
from visualizer import visualize

def load_map() -> None:
    filename = input("Enter name of file to read data from: ")
    hubs: list[Hub] = []
    connections: list[Connection] = []
    number_of_drones: int 
    hubs, connections, number_of_drones = parse_map(filename)
    for hub in hubs:
        hub.get_info()
    for connection in connections:
        connection.get_info()
    print(f"{number_of_drones} drones")
    visualize(hubs, connections)

load_map()