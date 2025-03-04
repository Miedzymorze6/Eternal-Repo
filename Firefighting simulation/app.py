import numpy as np
import pygame
import time
import math

# Constants for simulation grid
GRID_SIZE = 250
TREE, FIRE, EMPTY, HEAT, WATER = 1, 2, 0, 3, 4
FIRE_SPREAD_CHANCE = 0.6   # Base probability of fire spreading
HEAT_SPREAD_CHANCE = 0.3   # Heat spread probability

# Wind settings
WIND_DIRECTION = (0, 1)    # (dy, dx) e.g., wind blowing right
WIND_STRENGTH = 0.3       # Additional chance in wind direction

# Colors in RGB
COLORS = {
    EMPTY: (0, 0, 0),         # Black
    TREE: (0, 255, 0),        # Green
    FIRE: (255, 0, 0),        # Red
    HEAT: (169, 169, 169),    # Gray
    WATER: (0, 0, 255)        # Blue
}

# Pygame display settings
CELL_SIZE = 3                      # Size of each grid cell in pixels
SIM_WIDTH = GRID_SIZE * CELL_SIZE  # Simulation area width/height
SIM_HEIGHT = GRID_SIZE * CELL_SIZE

# UI panel sizes
LEFT_PANEL_WIDTH = 200
RIGHT_PANEL_WIDTH = 200
WINDOW_WIDTH = LEFT_PANEL_WIDTH + SIM_WIDTH + RIGHT_PANEL_WIDTH
WINDOW_HEIGHT = SIM_HEIGHT

# Pattern parameters (in grid cells)
PATTERN_SIZE = 15  # roughly the diameter/width of the pattern

# Global variables for simulation statistics
burned_history = []  # list of burned tree counts over simulation time
initial_tree_count = None

def initialize_forest(density=0.7):
    global initial_tree_count
    forest = np.random.choice([TREE, EMPTY], size=(GRID_SIZE, GRID_SIZE), p=[density, 1-density])
    initial_tree_count = np.count_nonzero(forest == TREE)
    center = GRID_SIZE // 2
    forest[center, center] = FIRE  # ignite center
    return forest

def spread_fire(forest):
    new_forest = forest.copy()
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            # Water cells block spread.
            if forest[y, x] == WATER:
                continue
            if forest[y, x] == FIRE:
                new_forest[y, x] = EMPTY  # fire burns out
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1),
                               (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < GRID_SIZE and 0 <= nx < GRID_SIZE:
                        if forest[ny, nx] == WATER:
                            continue
                        if forest[ny, nx] == TREE:
                            spread_chance = FIRE_SPREAD_CHANCE
                            if (dy, dx) == WIND_DIRECTION:
                                spread_chance += WIND_STRENGTH
                            if np.random.random() < spread_chance:
                                new_forest[ny, nx] = FIRE
                        elif forest[ny, nx] == EMPTY:
                            if np.random.random() < HEAT_SPREAD_CHANCE:
                                new_forest[ny, nx] = HEAT
            elif forest[y, x] == HEAT:
                if np.random.random() < 0.1:
                    new_forest[y, x] = EMPTY
    return new_forest

def draw_forest(screen, forest):
    # Draw simulation grid offset by LEFT_PANEL_WIDTH
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = COLORS[forest[y, x]]
            rect = pygame.Rect(LEFT_PANEL_WIDTH + x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            screen.fill(color, rect)

def draw_line_graph(screen, history):
    # Draw a simple line graph in the left panel showing burned trees over time.
    panel_rect = pygame.Rect(0, 0, LEFT_PANEL_WIDTH, WINDOW_HEIGHT)
    pygame.draw.rect(screen, (30, 30, 30), panel_rect)
    
    if len(history) < 2:
        return
    
    margin = 20
    graph_width = LEFT_PANEL_WIDTH - 2 * margin
    graph_height = WINDOW_HEIGHT - 2 * margin
    max_val = initial_tree_count if initial_tree_count else 1

    pygame.draw.line(screen, (200, 200, 200), (margin, margin), (margin, WINDOW_HEIGHT - margin), 2)
    pygame.draw.line(screen, (200, 200, 200), (margin, WINDOW_HEIGHT - margin), (LEFT_PANEL_WIDTH - margin, WINDOW_HEIGHT - margin), 2)
    
    n = len(history)
    x_step = graph_width / (n - 1)
    points = []
    for i, val in enumerate(history):
        y = WINDOW_HEIGHT - margin - (val / max_val) * graph_height
        x = margin + i * x_step
        points.append((x, y))
    
    if len(points) > 1:
        pygame.draw.lines(screen, (255, 255, 0), False, points, 2)

def draw_pattern_icons(screen, selected_pattern):
    start_x = LEFT_PANEL_WIDTH + SIM_WIDTH + 20
    start_y = 20
    icon_size = 50
    gap = 20
    patterns = ['square', 'circle', 'triangle', 'octagon']
    icons = {}
    font = pygame.font.SysFont(None, 20)
    for i, pattern in enumerate(patterns):
        rect = pygame.Rect(start_x, start_y + i * (icon_size + gap), icon_size, icon_size)
        color = (100, 100, 100) if pattern != selected_pattern else (150, 150, 150)
        pygame.draw.rect(screen, color, rect)
        center = (rect.x + icon_size//2, rect.y + icon_size//2)
        if pattern == 'square':
            size = 15
            pygame.draw.rect(screen, (0,0,255), (center[0]-size//2, center[1]-size//2, size, size), 0)
        elif pattern == 'circle':
            pygame.draw.circle(screen, (0,0,255), center, 15, 0)
        elif pattern == 'triangle':
            points = [(center[0], center[1]-15), (center[0]-15, center[1]+15), (center[0]+15, center[1]+15)]
            pygame.draw.polygon(screen, (0,0,255), points, 0)
        elif pattern == 'octagon':
            r = 15
            pts = []
            for j in range(8):
                angle = math.radians(45*j)
                pts.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
            pygame.draw.polygon(screen, (0,0,255), pts, 0)
        text = font.render(pattern, True, (255,255,255))
        screen.blit(text, (rect.x, rect.y + icon_size))
        icons[pattern] = rect
    return icons

def imprint_square(forest, grid_pos, size=PATTERN_SIZE):
    half = size // 2
    cx, cy = grid_pos
    for y in range(cy - half, cy + half + 1):
        for x in range(cx - half, cx + half + 1):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                forest[y, x] = WATER

def imprint_circle(forest, grid_pos, radius=PATTERN_SIZE//2):
    cx, cy = grid_pos
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                if math.sqrt((x-cx)**2 + (y-cy)**2) <= radius:
                    forest[y, x] = WATER

def imprint_triangle(forest, grid_pos, size=PATTERN_SIZE):
    cx, cy = grid_pos
    half = size // 2
    for y in range(size):
        span = int((y / size) * half)
        for x in range(cx - span, cx + span + 1):
            gy = cy - half + y
            if 0 <= x < GRID_SIZE and 0 <= gy < GRID_SIZE:
                forest[gy, x] = WATER

def imprint_octagon(forest, grid_pos, size=PATTERN_SIZE):
    cx, cy = grid_pos
    r = size // 2
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                if abs(x - cx) + abs(y - cy) <= r + r//2:
                    forest[y, x] = WATER

pattern_functions = {
    'square': imprint_square,
    'circle': imprint_circle,
    'triangle': imprint_triangle,
    'octagon': imprint_octagon
}

# ----------------------- Firefighter Agent -----------------------

class Firefighter:
    def __init__(self, x, y):
        self.x = x  # Grid x coordinate
        self.y = y  # Grid y coordinate
        self.speed = 10  # Moves one cell per update
        self.spray_range = 7  # Water spray range in pixels

    def update(self, forest):
        target = self.find_nearest_fire(forest)
        if target:
            tx, ty = target
            # Compute step direction toward the fire cell (using simple sign differences)
            dx = np.sign(tx - self.x)
            dy = np.sign(ty - self.y)

            # Move firefighter toward fire
            new_x = self.x + dx
            new_y = self.y + dy
            if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
                self.x = new_x
                self.y = new_y

            # Spray water in the direction of fire
            self.spray_water(forest, dx, dy)
        else:
            # If no fire is found, perform a random walk.
            self.random_walk()

    def spray_water(self, forest, dx, dy):
        """Sprays water in a straight line for `self.spray_range` pixels in direction (dx, dy)."""
        for i in range(1, self.spray_range + 1):
            water_x = self.x + dx * i
            water_y = self.y + dy * i
            if 0 <= water_x < GRID_SIZE and 0 <= water_y < GRID_SIZE:
                if forest[water_y, water_x] in {TREE, FIRE}:
                    forest[water_y, water_x] = WATER  # Convert fire/tree to water

    def find_nearest_fire(self, forest):
        min_distance = None
        target = None
        fire_indices = np.argwhere(forest == FIRE)
        if fire_indices.size == 0:
            return None
        for fy, fx in fire_indices:
            distance = abs(fx - self.x) + abs(fy - self.y)  # Manhattan distance
            if min_distance is None or distance < min_distance:
                min_distance = distance
                target = (fx, fy)
        return target

    def random_walk(self):
        dx, dy = np.random.choice([-1, 0, 1], size=2)
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.x = new_x
            self.y = new_y

    def draw(self, screen):
        color = (255, 255, 255)
        screen_x = LEFT_PANEL_WIDTH + self.x * CELL_SIZE + CELL_SIZE // 2
        screen_y = self.y * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, color, (screen_x, screen_y), CELL_SIZE + 1)

# ----------------------- Main Simulation -----------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Forest Fire Simulation with Firefighting Agents")
    clock = pygame.time.Clock()

    forest = initialize_forest()
    global burned_history
    burned_history = [0]

    # Number of firefighters to ensure 360-degree coverage
    NUM_FIREFIGHTERS = 24  # Adjust based on fire intensity and GRID_SIZE
    RADIUS = 30  # Distance from fire center

    # Fire center
    fire_x, fire_y = GRID_SIZE // 2, GRID_SIZE // 2

    # Place firefighters in a circular formation
    firefighters = [
        Firefighter(
            fire_x + int(RADIUS * math.cos(math.radians(angle))),
            fire_y + int(RADIUS * math.sin(math.radians(angle)))
        )
        for angle in range(0, 360, 360 // NUM_FIREFIGHTERS)
    ]


    running = True
    simulation_interval = 1/3  # seconds
    last_update_time = time.time()

    selected_pattern = None  # current selected pattern string, e.g., 'square'
    pattern_icons = {}

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx >= LEFT_PANEL_WIDTH + SIM_WIDTH:
                    for pattern, rect in pattern_icons.items():
                        if rect.collidepoint(mx, my):
                            selected_pattern = pattern
                            break
                elif LEFT_PANEL_WIDTH <= mx < LEFT_PANEL_WIDTH + SIM_WIDTH:
                    if selected_pattern:
                        grid_x = (mx - LEFT_PANEL_WIDTH) // CELL_SIZE
                        grid_y = my // CELL_SIZE
                        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                            pattern_functions[selected_pattern](forest, (grid_x, grid_y))
                            
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:
                    mx, my = pygame.mouse.get_pos()
                    if LEFT_PANEL_WIDTH <= mx < LEFT_PANEL_WIDTH + SIM_WIDTH and selected_pattern:
                        grid_x = (mx - LEFT_PANEL_WIDTH) // CELL_SIZE
                        grid_y = my // CELL_SIZE
                        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE:
                            pattern_functions[selected_pattern](forest, (grid_x, grid_y))
            
        current_time = time.time()
        if current_time - last_update_time >= simulation_interval:
            for _ in range(3):
                forest = spread_fire(forest)
            # Update firefighters each simulation step.
            for firefighter in firefighters:
                firefighter.update(forest)
                
            last_update_time = current_time
            current_tree_count = np.count_nonzero(forest == TREE)
            burned = initial_tree_count - current_tree_count
            burned_history.append(burned)
            if len(burned_history) > 100:
                burned_history.pop(0)
            
        screen.fill((0, 0, 0))
        draw_line_graph(screen, burned_history)
        draw_forest(screen, forest)
        right_panel_rect = pygame.Rect(LEFT_PANEL_WIDTH + SIM_WIDTH, 0, RIGHT_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(screen, (50, 50, 50), right_panel_rect)
        pattern_icons = draw_pattern_icons(screen, selected_pattern)
        
        # Draw firefighters on top of the simulation.
        for firefighter in firefighters:
            firefighter.draw(screen)
            
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
