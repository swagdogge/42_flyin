import pygame
import math
from connection import Connection
from hub import Hub

#SCREEN SETTINGS
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 700
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

def draw_connection(surface, hub_a, hub_b, capacity=1):
    """Draw a line between two hubs, thicker for higher capacity."""
    pygame.draw.line(
        surface,
        COLOR_CONNECTION,
        (hub_a.x, hub_a.y),
        (hub_b.x, hub_b.y),
        width=max(1, capacity * 2),
    )

def draw_hub(surface, hub, font, hovered=False):
    """Draw a hub circle with label. Start/end hubs get a colored ring."""
    color = COLOR_MAP.get(hub.color, COLOR_MAP["none"])
    if hovered:
        color = brighten(color, HOVER_BRIGHTEN)

    # outer ring for start/end
    if hub.is_start:
        pygame.draw.circle(surface, START_RING, (hub.x, hub.y), HUB_RADIUS + 5, width=3)
    if hub.is_end:
        pygame.draw.circle(surface, END_RING,   (hub.x, hub.y), HUB_RADIUS + 5, width=3)

    # main circle
    pygame.draw.circle(surface, color,       (hub.x, hub.y), HUB_RADIUS)
    pygame.draw.circle(surface, TEXT_COLOR,  (hub.x, hub.y), HUB_RADIUS, width=1)

    # label below the circle
    label = font.render(hub.name, True, TEXT_COLOR)
    rect  = label.get_rect(centerx=hub.x, top=hub.y + HUB_RADIUS + 4)
    surface.blit(label, rect)

def scale_hubs(hubs, margin=80):
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
        h.x = int(margin + (h.x - min_x) / span_x * (SCREEN_WIDTH - 2 * margin))
        h.y = int(margin + (h.y - min_y) / span_y * (SCREEN_HEIGHT - 2 * margin))


def visualize(hubs: list[Hub], connections: list[Connection]) -> None:
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("fly_in_visualizer")
    clock = pygame.time.Clock()

    # build name → hub lookup so connections can find their endpoints
    hub_map = {h.name: h for h in hubs}

    scale_hubs(hubs)
    running = True
    while running:
        screen.fill(COLOR_BG)

        for conn in connections:
            a = hub_map.get(conn.zone_a)
            b = hub_map.get(conn.zone_b)
            if a and b:
                draw_connection(screen, a, b, conn.max_link_capacity)
        for hub in hubs:
            pygame.draw.circle(screen, hub.color, (hub.x, hub.y), hub.max_drones)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit