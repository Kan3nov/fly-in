try:
    import models
    import pygame
except Exception as e:
    print(e)
    exit()

pygame.init()
FONT1 = pygame.font.Font(None, 15)
FONT2 = pygame.font.Font(None, 40)
FPS = 60
min_x: int
min_y: int
grid_width: int
grid_height: int
cell_width: int
cell_height: int


class Bird(pygame.sprite.Sprite, object):
    """Render and animate a drone as a bird sprite."""

    def __init__(self, cur_cord: tuple[int, int], drone: models.Drone):
        """Create an animated sprite for a drone.

        Args:
            cur_cord: Initial center position of the sprite in pixels.
            drone: Drone represented by this sprite.

        Returns:
            None.
        """
        super().__init__()
        self.image = pygame.image.load(
            "assets/bird_animation/00.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (32, 32))
        self.drone = drone
        self.rect = self.image.get_rect(center=cur_cord)
        self.movex = 0
        self.movey = 0
        self.stepx = 0
        self.stepy = 0
        self.steps = 0
        self.animation = 0.0

    def update(self, dest: tuple[int, int]) -> int:
        """Advance the animation and move toward the destination.

        Args:
            dest: Destination center in pixels, or None when idle.

        Returns:
            int: 1 while a move is in progress; otherwise, 0.
        """
        if dest:
            dist = (dest[0] - self.rect.centerx, dest[1] - self.rect.centery)
            self.steps += 1
            if self.stepx == 0:
                self.stepx = dist[0] / FPS
            if self.stepy == 0:
                self.stepy = dist[1] / FPS
        if self.movex >= 1 or self.movex <= -1:
            self.rect.x += (self.movex // 1)
            self.movex = (self.movex - self.movex // 1)
        if self.movey >= 1 or self.movey <= -1:
            self.rect.y += (self.movey // 1)
            self.movey = (self.movey - self.movey // 1)
        self.movex += self.stepx
        self.movey += self.stepy
        self.animation += 0.2
        if (self.animation >= 8):
            self.animation = 0
        self.image = pygame.transform.scale(pygame.image.load(
            f"assets/bird_animation/0{int(self.animation)}.png"
        ), (32, 32)).convert_alpha()
        if (dest):
            if (self.steps == FPS):
                self.rect.centerx = dest[0]
                self.rect.centery = dest[1]
                self.stepx = 0
                self.stepy = 0
                self.steps = 0
                self.movex = 0
                self.movey = 0
                return 0
            return (1)
        return 0


class Background(pygame.sprite.Sprite):
    """Render the full-screen simulation background."""

    def __init__(self, image_path: str):
        """Create a screen-sized background sprite.

        Args:
            image_path: Path to the background image.

        Returns:
            None.
        """
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (1920, 1080))
        self.rect = self.image.get_rect(topleft=(0, 0))


class Cloud(pygame.sprite.Sprite):
    """Render a labeled and optionally recolored zone sprite."""

    def __init__(self, image_path: str, zone: models.Zone):
        """Create a labeled sprite for a network zone.

        Args:
            image_path: Path to the zone image.
            zone: Zone whose name, color, and position are displayed.

        Returns:
            None.
        """
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (64, 64))
        name_surf = FONT1.render(zone.name, False, (225, 255, 235))

        new_width = max((self.image.get_width(), name_surf.get_width()))
        new_height = self.image.get_height() + name_surf.get_height()
        new_image = pygame.surface.Surface((new_width, new_height),
                                           pygame.SRCALPHA)
        new_image.blit(self.image, (0, 0))
        new_image.blit(name_surf, (0, self.image.get_rect().bottom))
        self.image = new_image.convert_alpha()
        if (zone.color in set(pygame.colordict.THECOLORS.keys())
                and not (zone.start or zone.end)):
            self.image = apply_color(self.image, pygame.Color(zone.color))
        self.rect = self.image.get_rect(
            center=get_zone_pos(zone))


def apply_color(surf: pygame.Surface, color: pygame.Color) -> pygame.Surface:
    filter = surf.copy()

    colored_pixels = []
    for x in range(filter.get_width()):
        for y in range(filter.get_height()):
            if filter.get_at((x, y))[3] != 0:
                colored_pixels.append((x, y))
    for pixel in colored_pixels:
        color.a = 80
        surf.set_at(pixel, color)
    filter.blit(surf, (0, 0))
    return filter


def draw_connections(screen: pygame.Surface,
                     zones: list[models.Zone]) -> None:
    """Draw each network connection between zones on the screen.

    Args:
        screen: Surface on which to draw the connections.
        zones: Zones whose neighbor relationships define the connections.

    Returns:
        None.
    """
    visited = set()
    for zone in zones:
        cord1 = get_zone_pos(zone)
        for neighbor in zone.neighbors:
            if neighbor.name in visited:
                continue
            cord2 = get_zone_pos(neighbor)
            pygame.draw.line(screen, (100, 100, 100), cord1, cord2, 3)
        visited.add(zone.name)


def get_zone_pos(zone: models.Zone) -> tuple[int, int]:
    """Convert a zone's grid coordinates to its screen-space center.

    Args:
        zone: Zone to position.

    Returns:
        tuple[int, int]: Pixel coordinates of the zone's center.
    """
    x = (zone.x - min_x) * cell_width + cell_width // 2
    y = (zone.y - min_y) * cell_height + cell_height // 2
    return (x, y)


def display_simulation(graph: models.Network) -> None:
    """Display an animated visualization of a completed network simulation.

    Args:
        graph: Network containing zones, drones, and recorded moves.

    Returns:
        None.
    """
    global min_x, min_y, grid_height, grid_width, cell_width, cell_height
    list_x: list[int] = []
    list_y: list[int] = []
    for zone in graph.zones.values():
        list_x.append(zone.x)
        list_y.append(zone.y)

    min_x = min(list_x)
    max_x = max(list_x)
    min_y = min(list_y)
    max_y = max(list_y)

    grid_width = abs(max_x - min_x) + 1
    grid_height = abs(max_y - min_y) + 1

    screen_width: int = 1920
    screen_height: int = 1080
    cell_width = screen_width // grid_width
    cell_height = screen_height // grid_height
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Fly in")

    zones = pygame.sprite.Group()
    for zone in graph.zones.values():
        if zone.start:
            zones.add(Cloud("assets/Terran.png", zone))
        elif zone.end:
            zones.add(Cloud("assets/Black_hole.png", zone))
        else:
            zones.add(Cloud("assets/cloud.png", zone))

    background = Background("assets/1.png")
    background_group = pygame.sprite.GroupSingle(background)
    drone_group = pygame.sprite.Group()
    init_cord = get_zone_pos(graph.start_hub)
    birds_dict = {}
    for drone in graph.drones:
        drone_surf = Bird(init_cord, drone)
        drone_group.add(drone_surf)
        birds_dict[drone.id] = drone_surf

    clock = pygame.time.Clock()
    turn = 0
    while (True):
        # Events handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_4:
                    pygame.quit()
                    exit()
        background_group.draw(screen)
        draw_connections(screen, graph.zones.values())
        zones.draw(screen)
        move_dict: dict = {}
        for bird in drone_group.sprites():
            move_dict[bird.drone.id] = None
        for move in graph.moves[turn]:
            if move == "":
                continue
            if (len(move.split("-")) == 3):
                drone_name, start_zone_name, dest_zone_name = move.split("-")
                drone_id = int(drone_name[1:])
                dest_zone = get_zone_pos(graph.zones[dest_zone_name])
                start_zone = get_zone_pos(graph.zones[start_zone_name])
                mid_point = ((dest_zone[0] + start_zone[0]) // 2,
                             (dest_zone[1] + start_zone[1]) // 2)
                move_dict[drone_id] = mid_point
            else:
                drone_name, dest_zone_name = move.split("-")
                drone_id = int(drone_name[1:])
                dest_zone = graph.zones[dest_zone_name]
                move_dict[drone_id] = get_zone_pos(dest_zone)
        next_turn = 1
        for drone_id, dest in move_dict.items():
            moved = birds_dict[drone_id].update(dest)
            if (moved == 1):
                next_turn = 0
        drone_group.draw(screen)
        if next_turn:
            turn += 1
        counter_circle = pygame.draw.circle(screen, "#bba9d4", (50, 50), 50)
        pygame.draw.circle(screen, "#8b8aea", (50, 50), 50, width=3)
        turns_text = FONT2.render(f"{turn}", True, "white")
        turns_rect = turns_text.get_rect(center=counter_circle.center)
        screen.blit(turns_text, turns_rect)

        pygame.display.update()
        clock.tick(FPS)
        if turn >= len(graph.moves):
            pygame.quit()
            exit()
