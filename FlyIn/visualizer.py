import pygame
import math
from network import Network
from connection import Connection
from hub import Hub
from cam import Cam

#SCREEN SETTINGS
FPS = 30
HUB_RADIUS = 24
FONT_SIZE = 14

COLOR_VALUES = {
    "green":  (80,  200, 120),
    "yellow": (240, 220,  60),
    "red":    (220,  70,  70),
    "blue":   ( 80, 140, 220),
    "gray":   (160, 160, 160),
    "none":   (180, 180, 180),
}

COLOR_BG = (30,  30,  40)
COLOR_CONNECTION = (100, 100, 120)
COLOR_TEXT      = (240, 240, 240)
COLOR_START      = ( 80, 220,  80)
COLOR_END     = (220, 200,  60)

def cammed(hub: Hub, cam: Cam) -> tuple[int, int]:
    return (
        int((hub.x - cam.x) * cam.zoom),
        int((hub.y - cam.y) * cam.zoom),
    )
 
def draw_connection(surface, hub_a, hub_b, cam: Cam, capacity=1):
    """Draw a line between two hubs, thicker for higher capacity."""
    pygame.draw.line(
        surface,
        COLOR_CONNECTION,
        cammed(hub_a, cam),
        cammed(hub_b, cam),
        width=max(1, capacity * 2),
    )

def draw_hub(surface, hub: Hub, font, cam: Cam):
    """Draw a hub circle with label. Start/end hubs get a colored ring."""
    color = COLOR_VALUES.get(hub.color, COLOR_VALUES["none"])

    # outer ring for start/end
    if hub.is_start:
        pygame.draw.circle(surface, COLOR_START, cammed(hub, cam), HUB_RADIUS + 5, width=3)
    if hub.is_end:
        pygame.draw.circle(surface, COLOR_END, cammed(hub, cam), HUB_RADIUS + 5, width=3)

    # main circle
    pygame.draw.circle(surface, color, cammed(hub, cam), HUB_RADIUS)
    pygame.draw.circle(surface, COLOR_TEXT, cammed(hub, cam), HUB_RADIUS, width=1)

    # label below the circle
    label = font.render(hub.name, True, COLOR_TEXT)
    x, y = cammed(hub, cam)
    rect = label.get_rect(
        centerx=x,
        top=y + HUB_RADIUS + 4
    )
    surface.blit(label, rect)

def scale_hubs(hubs, margin, screen_height, screen_width):
    """
    Scale hub coordinates from config-space to screen-space.
    Config coords can be small integers; this maps them to the window.
    """
    xs = [h.x for h in hubs]
    ys = [h.y for h in hubs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max(max_x - min_x, 1)
    span_y = max(max_y - min_y, 1)

    for h in hubs:
        h.x = int(margin + (h.x - min_x) / span_x * (screen_width - 2 * margin))
        h.y = int(margin + (h.y - min_y) / span_y * (screen_height - 2 * margin))


def visualize(network: Network) -> None:
    pygame.init()
    cam = Cam(0, 0, 1)
    info = pygame.display.Info()
    screen_width = info.current_w
    screen_height = info.current_h
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("fly_in_visualizer")
    font   = pygame.font.SysFont("Arial", FONT_SIZE)
    clock = pygame.time.Clock()

    # build name → hub lookup so connections can find their endpoints

    scale_hubs(network.hubs.values(), 80, screen_height, screen_width)
    running = True
    while running:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            cam.y -= int(screen_height / 100)
        if keys[pygame.K_DOWN]:
            cam.y += int(screen_height / 100)
        if keys[pygame.K_LEFT]:
            cam.x -= int(screen_width / 100)
        if keys[pygame.K_RIGHT]:
            cam.x += int(screen_width / 100)
        if keys[pygame.K_EQUALS]:
            cam.zoom += 0.01
        if keys[pygame.K_MINUS]:
            cam.zoom -= 0.01

        screen.fill(COLOR_BG)
        for conn in network.connections:
            a = network.hubs.get(conn.zone_a)
            b = network.hubs.get(conn.zone_b)
            if a and b:
                draw_connection(screen, a, b, cam, conn.max_link_capacity)
        for hub in network.hubs.values():
            draw_hub(screen, hub, font, cam)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()

#drone movement concept
#for turn in file #each line in the file represents one turn
#for each drone thats metioned in current tutns line
     #store the position of the next target and calculate step distance (total_distance_to_target / frames per turn )
#repeat for amount of frames per turn
     #for each drone that is mentioned in the current turns line
         #move the drone step distance towards target direction
