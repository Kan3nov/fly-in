try:
    import models
    import pygame
except Exception as e:
    print(e)
    exit()


class Bird(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = image_path
        self.rect = ...

    def update():
        ...


class Background(pygame.sprite.Sprite):
    def __init__(self, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (1920, 1080))
        self.rect = self.image.get_rect(topleft=(0, 0))


class Cloud(pygame.sprite.Sprite):
    def __init__(self, image_path: str, pos: tuple[int, int],
                 cell_width: int, cell_height: int):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(
            center=(pos[0] * cell_width + cell_width // 2,
                    pos[1] * cell_height + cell_height // 2))
        print((pos[0] * cell_width + cell_width // 2,
                    pos[1] * cell_height + cell_height // 2))

    def update():
        ...


def display_simulation(graph: models.Network):
    list_x = []
    list_y = []
    for name, zone in graph.zones.items():
        list_x.append(zone.x)
        list_y.append(zone.y)

    min_x = min(list_x)
    min_y = min(list_y)
    max_x = max(list_x)
    max_y = max(list_y)

    grid_width = abs(max_x - min_x)
    grid_height = abs(max_y - min_y)

    pygame.init()
    screen_width = 1920
    screen_height = 1080
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Fly in")
    cell_width = screen_width // grid_width
    cell_height = screen_height // grid_height
    zones = pygame.sprite.Group()
    for zone in graph.zones.values():
        x = zone.x - min_x
        y = zone.y - min_y
        zones.add(Cloud("assets/cloud.png", (x, y), cell_width, cell_height))

    background = Background("assets/sky.png")
    background_group = pygame.sprite.GroupSingle(background)

    clock = pygame.time.Clock()

    while (True):
        # Events handler
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        background_group.draw(screen)
        zones.draw(screen)
        pygame.display.update()
        clock.tick(60)
