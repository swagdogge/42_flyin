import pygame
from network import Network
from hub import Hub
from cam import Cam

FPS = 30
FRAMES_PER_TURN = FPS
HUB_RAD = 50
FONT_SIZE = 14

COLOR_VALUES = {
    "green": (80, 200, 120), "yellow": (240, 220, 60), "red": (220, 70, 70),
    "blue": (80, 140, 220), "gray": (160, 160, 160), "none": (180, 180, 180),
}
COLOR_BG = (30,  30,  40)
COLOR_CONNECTION = (100, 100, 120)
COLOR_TEXT = (240, 240, 240)
COLOR_START = (80,  220,  80)
COLOR_END = (220, 200,  60)


def cammed(hub: Hub, cam: Cam) -> tuple[int, int]:
    """Convert hub coords to camera adjusted screen coords."""
    return (int((hub.x - cam.x) * cam.zoom), int((hub.y - cam.y) * cam.zoom))


def scale_hubs(
    hubs: list[Hub],
    margin: int,
    screen_w: int,
    screen_h: int,
) -> None:
    """Fit hub coords into the screen preserving aspect ratio, centered."""
    xs, ys = [h.x for h in hubs], [h.y for h in hubs]
    min_x, min_y = min(xs), min(ys)
    span_x = max(max(xs) - min_x, 1)
    span_y = max(max(ys) - min_y, 1)

    usable_w = screen_w - 2 * margin
    usable_h = screen_h - 2 * margin

    scale = min(usable_w / span_x, usable_h / span_y)

    # Centre the map in the remaining space after scaling
    offset_x = margin + (usable_w - span_x * scale) / 2
    offset_y = margin + (usable_h - span_y * scale) / 2

    for h in hubs:
        h.x = offset_x + (h.x - min_x) * scale
        h.y = offset_y + (h.y - min_y) * scale


def build_turns(output_lines: list[str], start_hub: str,
                nb_drones: int) -> list[dict[str, str]]:
    """Build per-turn drone position dicts from simulation output."""
    current: dict[str, str] = {f"D{i+1}": start_hub for i in range(nb_drones)}
    turns: list[dict[str, str]] = [dict(current)]
    for line in output_lines:
        for token in line.strip().split():
            parts = token.split("-")
            if len(parts) == 3:
                current[parts[0]] = f"{parts[1]}>{parts[2]}"
            else:
                current[parts[0]] = parts[1]
        turns.append(dict(current))
    return turns


def resolve_pos(pos: str, network: Network, cam: Cam) -> tuple[int, int]:
    """get screen coordinates for a hub name or 'a>b' transit string."""
    if ">" in pos:
        a, b = network.hubs[pos.split(">")[0]], network.hubs[pos.split(">")[1]]
        return (int(((a.x + b.x) / 2 - cam.x) * cam.zoom),
                int(((a.y + b.y) / 2 - cam.y) * cam.zoom))
    return cammed(network.hubs[pos], cam)


def visualize(network: Network, output_lines: list[str]) -> None:
    """
    Visualizer with step / debug mode and animated playback.

    SPACE: play/pause animation
    BACKSPACE/RIGHT: step back/forward one turn (and pauses)
    WASD: move camera +/-: zoom   ESC: quit

    Input:
    Network: Network object containing all hubs and connections
    output_lines: list of drone instructions (one line per turn)
    """
    pygame.init()

    # DISPLAY / TEXT / TIME
    info = pygame.display.Info()
    W, H = info.current_w, info.current_h
    screen = pygame.display.set_mode((W, H))
    hub_surface = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.display.set_caption("fly_in_visualizer")
    font = pygame.font.SysFont("Arial", FONT_SIZE)
    clock = pygame.time.Clock()

    # CAMERA
    cam = Cam(0, 0, 1)
    zoom_speed = 1.02
    cam_dirty = True

    # SCALE HUBS
    screen.fill(COLOR_BG)
    loading = font.render("Scaling Hubs...", True, COLOR_TEXT)
    screen.blit(loading, loading.get_rect(centerx=W // 2, centery=H // 2))
    pygame.display.flip()
    scale_hubs(list(network.hubs.values()), 80, W, H)
    start_hub = next(h.name for h in network.hubs.values() if h.is_start)

    # LABEL DRONES
    drone_labels: set[str] = set()
    for line in output_lines:
        for token in line.strip().split():
            drone_labels.add(token.split("-")[0])

    # BUILD TURNS
    screen.fill(COLOR_BG)
    loading = font.render("Building Turns...", True, COLOR_TEXT)
    screen.blit(loading, loading.get_rect(centerx=W // 2, centery=H // 2))
    pygame.display.flip()
    turns = build_turns(output_lines, start_hub, len(drone_labels))
    total = len(turns)
    current_turn = 0
    current_frame = 0
    playing = False
    display_hubs: bool = True
    running = True

    # SORT CONNECTIONS loading screen
    screen.fill(COLOR_BG)
    loading = font.render("Sorting Connections...", True, COLOR_TEXT)
    screen.blit(loading, loading.get_rect(centerx=W // 2, centery=H // 2))
    pygame.display.flip()
    sorted_conn = sorted(
        network.connections,
        key=lambda conn: conn.max_link_capacity
    )

    # KEYBOARD INPUT
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    playing = False
                    current_frame = 0
                    current_turn = min(current_turn + 1, total - 1)
                elif event.key == pygame.K_LEFT:
                    playing = False
                    current_frame = 0
                    current_turn = max(current_turn - 1, 0)
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                    current_frame = 0
                elif event.key == pygame.K_h:
                    display_hubs = not display_hubs
                    cam_dirty = True
                elif event.key == pygame.K_ESCAPE:
                    running = False

        # CAMERA CONTROLS (WASD)
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * W // 100
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * H // 100
        if dx or dy:
            cam.x += dx
            cam.y += dy
            cam_dirty = True

        # CAMERA CONTROLS (ZOOM)
        if keys[pygame.K_EQUALS]:
            cam.zoom *= zoom_speed
            cam_dirty = True
        if keys[pygame.K_MINUS]:
            cam.zoom /= zoom_speed
            cam_dirty = True
        cam.zoom = max(0.05, cam.zoom)

        # INTERPOLATION
        t = current_frame / FRAMES_PER_TURN if playing else 0.0
        pos_now = turns[current_turn]
        pos_next = turns[min(current_turn + 1, total - 1)]

        # CONNECTIONS DISPLAY
        if cam_dirty:
            hub_surface.fill((0, 0, 0, 0))

            max_cap = max(
                (c.max_link_capacity for c in network.connections), default=1)

            for conn in sorted_conn:
                a, b = network.hubs.get(
                    conn.zone_a), network.hubs.get(conn.zone_b)
                if a and b:
                    cap_t = max(
                        0.0, min(1.0, conn.max_link_capacity / max_cap))
                    color = (
                        int(220 * (1 - cap_t)),
                        int(40 + 160 * cap_t),
                        int(40 + 80 * cap_t),
                    )
                    pygame.draw.line(hub_surface, color,
                                     cammed(a, cam), cammed(b, cam),
                                     width=max(1, conn.max_link_capacity + 1))

        # HUBS DISPLAY
            if display_hubs:
                for hub in network.hubs.values():

                    color = COLOR_VALUES.get(hub.color, COLOR_VALUES["none"])
                    adj_rad = HUB_RAD * 0.2 * cam.zoom

                    if hub.is_start:
                        pygame.draw.circle(
                            hub_surface, COLOR_START,
                            cammed(hub, cam), adj_rad + 5, 3)

                    if hub.is_end:
                        pygame.draw.circle(
                            hub_surface, COLOR_END,
                            cammed(hub, cam), adj_rad + 5, 3)

                    pygame.draw.circle(
                        hub_surface, color, cammed(hub, cam), adj_rad)

                    pygame.draw.circle(
                        hub_surface, COLOR_TEXT, cammed(hub, cam), adj_rad, 1)

                    lbl = font.render(hub.name, True, COLOR_TEXT)
                    cx, cy = cammed(hub, cam)
                    hub_surface.blit(
                        lbl, lbl.get_rect(centerx=cx, top=cy + HUB_RAD + 4))

                cam_dirty = False

        screen.fill(COLOR_BG)
        screen.blit(hub_surface, (0, 0))

        # DRONES DISPLAY
        for label in sorted(drone_labels):
            ax, ay = resolve_pos(pos_now.get(label, start_hub), network, cam)
            bx, by = resolve_pos(pos_next.get(label, start_hub), network, cam)
            dx = int(ax + (bx - ax) * t)
            dy = int(ay + (by - ay) * t)
            pygame.draw.circle(screen, (255, 220, 50), (dx, dy), 10)
            screen.blit(
                font.render(label, True, COLOR_TEXT), (dx + 12, dy - 8))

        # INFO / CONTROLS
        if playing:
            mode = "PLAYING"
        else:
            mode = "PAUSED"
        screen.blit(font.render(
            f"Turn {current_turn}/{total - 1}  [{mode}]"
            f"SPACE: play/pause RIGHT: step LEFT: back WASD: pan  +/-: zoom",
            True, COLOR_TEXT), (12, 12))

        # TURN CONTROLS
        if playing:
            current_frame += 1
            if current_frame >= FRAMES_PER_TURN:
                current_frame = 0
                if current_turn < total - 1:
                    current_turn += 1
                else:
                    playing = False

        # REFRESH
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
