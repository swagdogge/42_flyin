import pygame
from network import Network
from hub import Hub
from cam import Cam

FPS = 30
FRAMES_PER_TURN = FPS
HUB_RADIUS = 24
FONT_SIZE = 14

COLOR_VALUES = {
    "green": (80, 200, 120), "yellow": (240, 220, 60), "red": (220, 70, 70),
    "blue": (80, 140, 220), "gray": (160, 160, 160), "none": (180, 180, 180),
}
COLOR_BG         = (30,  30,  40)
COLOR_CONNECTION = (100, 100, 120)
COLOR_TEXT       = (240, 240, 240)
COLOR_START      = (80,  220,  80)
COLOR_END        = (220, 200,  60)


def cammed(hub: Hub, cam: Cam) -> tuple[int, int]:
    """Convert hub world coords to screen coords."""
    return (int((hub.x - cam.x) * cam.zoom), int((hub.y - cam.y) * cam.zoom))


def scale_hubs(hubs: list[Hub], margin: int, screen_w: int, screen_h: int) -> None:
    """Fit hub coords into the screen."""
    xs, ys = [h.x for h in hubs], [h.y for h in hubs]
    span_x, span_y = max(max(xs) - min(xs), 1), max(max(ys) - min(ys), 1)
    for h in hubs:
        h.x = int(margin + (h.x - min(xs)) / span_x * (screen_w - 2 * margin))
        h.y = int(margin + (h.y - min(ys)) / span_y * (screen_h - 2 * margin))


def build_turns(output_lines: list[str], start_hub: str,
                nb_drones: int) -> list[dict[str, str]]:
    """Build per-turn drone position dicts from simulation output."""
    current: dict[str, str] = {f"D{i+1}": start_hub for i in range(nb_drones)}
    turns: list[dict[str, str]] = [dict(current)]
    for line in output_lines:
        for token in line.strip().split():
            parts = token.split("-")
            current[parts[0]] = f"{parts[1]}>{parts[2]}" if len(parts) == 3 else parts[1]
        turns.append(dict(current))
    return turns


def resolve_pos(pos: str, network: Network, cam: Cam) -> tuple[int, int]:
    """Screen coords for a hub name or 'a>b' transit string."""
    if ">" in pos:
        a, b = network.hubs[pos.split(">")[0]], network.hubs[pos.split(">")[1]]
        return (int(((a.x + b.x) / 2 - cam.x) * cam.zoom),
                int(((a.y + b.y) / 2 - cam.y) * cam.zoom))
    return cammed(network.hubs[pos], cam)


def visualize(network: Network, output_lines: list[str]) -> None:
    """Visualizer with step mode and animated playback.

    SPACE: play/pause animation
    BACKSPACE/RIGHT: step back/forward one turn (also pauses)
    Arrow keys: pan   +/-: zoom   ESC: quit
    """
    pygame.init()
    info = pygame.display.Info()
    W, H = info.current_w, info.current_h
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("fly_in_visualizer")
    font = pygame.font.SysFont("Arial", FONT_SIZE)
    clock = pygame.time.Clock()
    cam = Cam(0, 0, 1)

    scale_hubs(list(network.hubs.values()), 80, W, H)
    start_hub = next(h.name for h in network.hubs.values() if h.is_start)

    drone_labels: set[str] = set()
    for line in output_lines:
        for token in line.strip().split():
            drone_labels.add(token.split("-")[0])

    turns = build_turns(output_lines, start_hub, len(drone_labels))
    total = len(turns)
    current_turn = 0
    current_frame = 0
    playing = False

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                    current_frame = 0
                elif event.key == pygame.K_RIGHT:
                    playing = False
                    current_frame = 0
                    current_turn = min(current_turn + 1, total - 1)
                elif event.key == pygame.K_LEFT:
                    playing = False
                    current_frame = 0
                    current_turn = max(current_turn - 1, 0)

        keys = pygame.key.get_pressed()
        cam.x += (keys[pygame.K_d] - keys[pygame.K_a]) * W // 100
        cam.y += (keys[pygame.K_s] - keys[pygame.K_w]) * H // 100
        cam.zoom = max(0.05, cam.zoom + (keys[pygame.K_EQUALS] - keys[pygame.K_MINUS]) * 0.01)

        # interpolation factor: 0.0 at start of turn, 1.0 at end
        t = current_frame / FRAMES_PER_TURN if playing else 0.0
        pos_now = turns[current_turn]
        pos_next = turns[min(current_turn + 1, total - 1)]

        screen.fill(COLOR_BG)

        for conn in network.connections:
            a, b = network.hubs.get(conn.zone_a), network.hubs.get(conn.zone_b)
            if a and b:
                pygame.draw.line(screen, COLOR_CONNECTION,
                                 cammed(a, cam), cammed(b, cam),
                                 width=max(1, conn.max_link_capacity * 2))

        for hub in network.hubs.values():
            color = COLOR_VALUES.get(hub.color, COLOR_VALUES["none"])
            if hub.is_start:
                pygame.draw.circle(screen, COLOR_START, cammed(hub, cam), HUB_RADIUS + 5, 3)
            if hub.is_end:
                pygame.draw.circle(screen, COLOR_END, cammed(hub, cam), HUB_RADIUS + 5, 3)
            pygame.draw.circle(screen, color, cammed(hub, cam), HUB_RADIUS)
            pygame.draw.circle(screen, COLOR_TEXT, cammed(hub, cam), HUB_RADIUS, 1)
            lbl = font.render(hub.name, True, COLOR_TEXT)
            cx, cy = cammed(hub, cam)
            screen.blit(lbl, lbl.get_rect(centerx=cx, top=cy + HUB_RADIUS + 4))

        for label in sorted(drone_labels):
            ax, ay = resolve_pos(pos_now.get(label, start_hub), network, cam)
            bx, by = resolve_pos(pos_next.get(label, start_hub), network, cam)
            dx = int(ax + (bx - ax) * t)
            dy = int(ay + (by - ay) * t)
            pygame.draw.circle(screen, (255, 220, 50), (dx, dy), 10)
            screen.blit(font.render(label, True, COLOR_TEXT), (dx + 12, dy - 8))

        mode = "PLAYING" if playing else "PAUSED"
        screen.blit(font.render(
            f"Turn {current_turn}/{total - 1}  [{mode}]  "
            f"SPACE: play/pause  RIGHT: step  LEFT: back  WASD: pan  +/-: zoom",
            True, COLOR_TEXT), (12, 12))

        if playing:
            current_frame += 1
            if current_frame >= FRAMES_PER_TURN:
                current_frame = 0
                if current_turn < total - 1:
                    current_turn += 1
                else:
                    playing = False

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()