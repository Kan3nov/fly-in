try:
    import models
    import pygame
except Exception as e:
    print(e)
    exit()

pygame.init()
FONT = pygame.font.Font(None, 15)


class Bird(pygame.sprite.Sprite):
    def __init__(self, cur_cord: tuple[int, int], drone: models.Drone):
        super().__init__()
        self.image = pygame.image.load(
            "assets/bird_animation/00.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (32, 32))
        self.drone = drone
        self.rect = self.image.get_rect(topleft=cur_cord)
        self.movex = 0
        self.movey = 0
        self.animation = 0

    def update(self, dist: tuple[int, int]) -> int:
        if (dist == (0, 0)):
            self.movex = 0
            self.movey = 0
            return 0
        self.movex += dist[0] / 60
        self.movey += dist[1] / 60
        if self.movex >= 1:
            self.rect.x += dist[0]
            self.movex -= 1
        if self.movey >= 1:
            self.rect.y += dist[1]
            self.movey -= 1
        self.animation += 0.2
        if (self.animation >= 8):
            self.animation = 0
        self.image = pygame.transform.scale(pygame.image.load(
            f"assets/bird_animation/0{self.animation // 1}.png"
        ), (32, 32))
        return (1)


class Background(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (1920, 1080))
        self.rect = self.image.get_rect(topleft=(0, 0))


class Cloud(pygame.sprite.Sprite):
    def __init__(self, image_path: str, zone: models.Zone):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (64, 64))
        self.name= "hello"

        name_surf = FONT.render(zone.name, False, (225, 255, 235))

        new_width = max((self.image.get_width(), name_surf.get_width()))
        new_height = self.image.get_height() + name_surf.get_height()
        new_image = pygame.surface.Surface((new_width, new_height),
                                           pygame.SRCALPHA)
        new_image.blit(self.image, (0, 0))
        new_image.blit(name_surf, (0, self.image.get_rect().bottom))
        self.image = new_image.convert_alpha()
        if zone.color in set(pygame.colordict.THECOLORS.keys()):
            self.image = color_swap(self.image, (242, 241, 231), zone.color)
        self.rect = self.image.get_rect(
            center=get_zone_pos(zone))

    def update():
        ...


def color_swap(surf: pygame.Surface, old_c: pygame.Color, new_c: pygame.Color):
    img_copy = pygame.Surface(surf.get_size())
    img_copy.fill(new_c)
    trans_pixels = []
    for x in range(surf.get_width()):
        for y in range(surf.get_height()):
            if surf.get_at((x, y))[3] == 0:
                trans_pixels.append((x, y))
    surf.set_colorkey(old_c)
    img_copy.blit(surf, (0, 0))
    for x, y in trans_pixels:
        img_copy.set_at((x, y), (0, 0, 0, 0))
    return img_copy.convert_alpha()


def draw_connections(screen: pygame.Surface,
                     zones: list[models.Zone]) -> None:
    visited = set()
    for zone in zones:
        cord1 = get_zone_pos(zone)
        for neighbor in zone.neighbors:
            if neighbor.name in visited:
                continue
            cord2 = get_zone_pos(neighbor)
            pygame.draw.line(screen, (100, 100, 100), cord1, cord2, 3)
        visited.add(zone.name)


def get_zone_pos(zone: models.Zone):
    x = (zone.x - min_x) * cell_width + cell_width // 2
    y = (zone.y - min_y) * cell_height + cell_height // 2
    return (x, y)


def display_simulation(graph: models.Network):
    global min_x, min_y, grid_height, grid_width, cell_width, cell_height
    list_x: list[int] = []
    list_y: list[int] = []
    for name, zone in graph.zones.items():
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

    background = Background("assets/sky.png")
    background_group = pygame.sprite.GroupSingle(background)
    drone_group = pygame.sprite.Group()
    init_cord = get_zone_pos(graph.start_hub)
    for drone in graph.drones:
        drone_surf = Bird(init_cord, drone)
        drone_group.add(drone_surf)

    clock = pygame.time.Clock()

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
        for bird in drone_group:
            bird.update()
        pygame.display.update()
        clock.tick(60)
