import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button
from mpl_toolkits.mplot3d import Axes3D  # For 3D plotting

# ============================
# Global Simulation Parameters
# ============================

# Simulation area (e.g., meters or kilometers)
area_min, area_max = 0, 100

# Base terrain parameters
terrain_base = 50            # base elevation (meters)
terrain_amplitude = 10       # amplitude scale (meters)
terrain_frequency = 0.1      # base frequency for components

# Time parameters
years = 50      # total simulation years (max)
dt = 1          # time step (years)
# We will use a global simulation time variable (in years)
current_year = 0

# CO₂ conversion (kg CO₂ per kg biomass)
conversion_factor = 1.65

# Initial tree density (number per axis; total trees = density²)
initial_tree_density = 10

# Initial terrain complexity (multiplier for random amplitudes)
initial_terrain_complexity = 1.0

# Grass simulation parameters
grass_max_height = 2.0      # maximum grass height (m)
grass_growth_rate = 0.1     # growth rate (m/year)
grass_grazing_prob = 0.05   # probability per update that a cell is grazed
grass_grazed_height = 0.2   # height when grazed
grass_grid_points = 20      # resolution for grass grid

# =============================
# Define Lakes & Barren Areas
# =============================
lakes = [
    {'center': (30, 30), 'radius': 15, 'growth_multiplier': 1.2},
    {'center': (70, 80), 'radius': 10, 'growth_multiplier': 1.15}
]
barren = [
    {'center': (80, 20), 'radius': 15, 'growth_multiplier': 0.8},
    {'center': (20, 70), 'radius': 10, 'growth_multiplier': 0.8}
]

def get_growth_multiplier(x, y):
    """
    Return a growth multiplier for a given (x, y) location.
    Lakes promote growth; barren areas reduce growth.
    """
    for region in lakes:
        cx, cy = region['center']
        if np.hypot(x - cx, y - cy) <= region['radius']:
            return region['growth_multiplier']
    for region in barren:
        cx, cy = region['center']
        if np.hypot(x - cx, y - cy) <= region['radius']:
            return region['growth_multiplier']
    return 1.0

# =============================
# Terrain Generation Functions
# =============================
terrain_components = []  # List to hold random sine–cosine components

def generate_terrain_components(complexity_factor):
    """Generate several random terrain components."""
    np.random.seed(42)  # reproducible terrain details
    components = []
    n_components = 3  # number of components
    for i in range(n_components):
        amplitude = terrain_amplitude * complexity_factor * np.random.uniform(0.5, 1.5)
        frequency = terrain_frequency * np.random.uniform(0.5, 1.5)
        phase_x = np.random.uniform(0, 2*np.pi)
        phase_y = np.random.uniform(0, 2*np.pi)
        components.append({'amplitude': amplitude,
                           'frequency': frequency,
                           'phase_x': phase_x,
                           'phase_y': phase_y})
    return components

def terrain_elevation(x, y):
    """Compute the terrain elevation at (x,y) using the random components."""
    elev = terrain_base
    for comp in terrain_components:
        elev += comp['amplitude'] * np.sin(comp['frequency'] * x + comp['phase_x']) * \
                np.cos(comp['frequency'] * y + comp['phase_y'])
    return elev

# Build a mesh grid for the terrain surface
terrain_grid_points = 50
x_terrain = np.linspace(area_min, area_max, terrain_grid_points)
y_terrain = np.linspace(area_min, area_max, terrain_grid_points)
X_terrain, Y_terrain = np.meshgrid(x_terrain, y_terrain)

def compute_terrain_surface():
    """Compute Z values over the mesh grid."""
    Z = np.array([[terrain_elevation(x, y) for x in x_terrain] for y in y_terrain])
    return Z

def compute_growth_potential_map():
    """
    Create a map of growth multipliers (from lakes and barren areas)
    over the terrain grid.
    """
    GP = np.ones_like(X_terrain)
    for i in range(X_terrain.shape[0]):
        for j in range(X_terrain.shape[1]):
            GP[i, j] = get_growth_multiplier(X_terrain[i, j], Y_terrain[i, j])
    return GP

# =============================
# Tree Species Parameters
# =============================
species_params = {
    "Oak":   {"H_max": 25.0, "growth_rate": 0.2, "t_mid": 20, "color": "saddlebrown", "biomass_factor": 0.12},
    "Pine":  {"H_max": 30.0, "growth_rate": 0.3, "t_mid": 15, "color": "darkgreen", "biomass_factor": 0.10},
    "Birch": {"H_max": 20.0, "growth_rate": 0.25, "t_mid": 18, "color": "yellowgreen", "biomass_factor": 0.09}
}
species_list = list(species_params.keys())

# =============================
# Initialize Tree Population
# =============================
trees = []  # List to hold tree dictionaries

def initialize_trees(tree_density):
    """
    Place trees on a jittered grid.
    tree_density: number of trees along each axis.
    """
    global trees
    trees = []
    margin = 10
    x_positions = np.linspace(area_min + margin, area_max - margin, tree_density)
    y_positions = np.linspace(area_min + margin, area_max - margin, tree_density)
    xx, yy = np.meshgrid(x_positions, y_positions)
    positions = np.column_stack((xx.ravel(), yy.ravel()))
    jitter = np.random.uniform(-2, 2, positions.shape)
    positions += jitter
    
    for pos in positions:
        species = np.random.choice(species_list)
        params = species_params[species]
        growth_rate_var = np.random.uniform(-0.05, 0.05)
        t_mid_var = np.random.uniform(-3, 3)
        tree = {
            'x': pos[0],
            'y': pos[1],
            'species': species,
            'H_max': params["H_max"],
            'growth_rate': params["growth_rate"] + growth_rate_var,
            't_mid': params["t_mid"] + t_mid_var,
            'color': params["color"],
            'biomass_factor': params["biomass_factor"]
        }
        trees.append(tree)

initialize_trees(initial_tree_density)

# =============================
# Initialize Grass Population
# =============================
grass_cells = []  # List to hold grass cell dictionaries

def initialize_grass():
    """Create a grid of grass cells over the simulation area."""
    global grass_cells
    grass_cells = []
    x_grass = np.linspace(area_min, area_max, grass_grid_points)
    y_grass = np.linspace(area_min, area_max, grass_grid_points)
    XX, YY = np.meshgrid(x_grass, y_grass)
    positions = np.column_stack((XX.ravel(), YY.ravel()))
    for pos in positions:
        cell = {
            'x': pos[0],
            'y': pos[1],
            'height': np.random.uniform(0.5, 1.0),  # initial height in meters
            'state': 'normal',  # 'normal' or 'grazed'
            'grazing_end': None
        }
        grass_cells.append(cell)

initialize_grass()

# =============================
# Global History for CO₂ Plot
# =============================
co2_history = []  # Total CO₂ sequestered at each update
species_history = {s: [] for s in species_list}  # For species stats if needed

# =============================
# Set Up Figure, Sliders, and Buttons
# =============================
fig = plt.figure(figsize=(16, 8))

# 3D axis for terrain, trees, and grass
ax1 = fig.add_subplot(121, projection='3d')
ax1.set_title("Forest & Grass Growth on Complex Terrain")
ax1.set_xlabel("X (location)")
ax1.set_ylabel("Y (location)")
ax1.set_zlabel("Elevation + Vegetation Height")
ax1.set_xlim(area_min, area_max)
ax1.set_ylim(area_min, area_max)
z_min = terrain_base - terrain_amplitude - 5
z_max = terrain_base + terrain_amplitude + max([tree['H_max'] for tree in trees]) + 20
ax1.set_zlim(z_min, z_max)

# 2D axis for CO₂ sequestration & species info
ax2 = fig.add_subplot(122)
ax2.set_title("CO₂ Sequestration & Species Stats")
ax2.set_xlabel("Time (years)")
ax2.set_ylabel("Total CO₂ Sequestered (kg)")
ax2.set_xlim(0, years)
ax2.set_ylim(0, 1.5e6)  # Adjust as needed

# Sliders for tree density and terrain complexity
ax_slider_density = plt.axes([0.15, 0.02, 0.3, 0.03])
slider_density = Slider(ax_slider_density, "Tree Density", 5, 20, valinit=initial_tree_density, valstep=1)

ax_slider_terrain = plt.axes([0.60, 0.02, 0.3, 0.03])
slider_terrain = Slider(ax_slider_terrain, "Terrain Complexity", 0.5, 2.0, valinit=initial_terrain_complexity)

# Buttons for pause/resume and restart
ax_pause = plt.axes([0.02, 0.9, 0.1, 0.05])
pause_button = Button(ax_pause, "Pause")
ax_restart = plt.axes([0.02, 0.8, 0.1, 0.05])
restart_button = Button(ax_restart, "Restart")

# =============================
# Slider Callback Functions
# =============================
def update_tree_density(val):
    new_density = int(slider_density.val)
    initialize_trees(new_density)
    co2_history.clear()  # Reset history when trees are reinitialized

slider_density.on_changed(update_tree_density)

def update_terrain_complexity(val):
    global terrain_components, Z_terrain
    comp = slider_terrain.val
    terrain_components = generate_terrain_components(comp)
    Z_terrain = compute_terrain_surface()

slider_terrain.on_changed(update_terrain_complexity)

# Initialize terrain components and surface
terrain_components = generate_terrain_components(initial_terrain_complexity)
Z_terrain = compute_terrain_surface()
growth_potential_map = compute_growth_potential_map()

# =============================
# Button Callback Functions
# =============================
paused = False
def toggle_pause(event):
    global paused
    if paused:
        anim.event_source.start()
        pause_button.label.set_text("Pause")
        paused = False
    else:
        anim.event_source.stop()
        pause_button.label.set_text("Resume")
        paused = True

pause_button.on_clicked(toggle_pause)

def restart_simulation(event):
    global current_year, co2_history
    current_year = 0
    co2_history.clear()
    initialize_grass()
    # Optionally, reinitialize trees:
    # initialize_trees(int(slider_density.val))
    # Restart the animation event source if paused
    if paused:
        pause_button.label.set_text("Pause")
        anim.event_source.start()
        paused = False

restart_button.on_clicked(restart_simulation)

# =============================
# Animation Update Function
# =============================
def update(frame):
    global current_year
    t = current_year  # use our own simulation time
    ax1.cla()  # Clear 3D axis for fresh drawing
    ax2.cla()  # Clear 2D axis

    # --- 3D Plot: Terrain, Trees, and Grass ---
    ax1.set_title(f"Vegetation Growth at Year {t:.1f}")
    ax1.set_xlabel("X (location)")
    ax1.set_ylabel("Y (location)")
    ax1.set_zlabel("Elevation + Vegetation Height")
    ax1.set_xlim(area_min, area_max)
    ax1.set_ylim(area_min, area_max)
    ax1.set_zlim(z_min, z_max)

    # Plot terrain surface
    surf = ax1.plot_surface(X_terrain, Y_terrain, Z_terrain, cmap="terrain",
                            alpha=0.5, linewidth=0, antialiased=False)
    # Overlay contour for growth potential (red = poor, green = good)
    gp_map = compute_growth_potential_map()
    cp = ax1.contourf(X_terrain, Y_terrain, gp_map, zdir='z', offset=z_min,
                      cmap='RdYlGn', alpha=0.5)
    
    total_CO2 = 0
    species_CO2 = {s: {'total': 0, 'count': 0} for s in species_list}
    
    # Plot trees
    for tree in trees:
        x, y = tree['x'], tree['y']
        base_elev = terrain_elevation(x, y)
        env_mult = get_growth_multiplier(x, y)
        effective_growth_rate = tree['growth_rate'] * env_mult
        h = tree['H_max'] / (1 + np.exp(-effective_growth_rate * (t - tree['t_mid'])))
        # Draw tree trunk
        ax1.plot([x, x], [y, y], [base_elev, base_elev + h], color=tree['color'], lw=2)
        ax1.scatter(x, y, base_elev + h, color=tree['color'], s=30)
        # CO₂ sequestration (biomass ~ height³)
        co2_tree = conversion_factor * tree['biomass_factor'] * (h ** 3)
        total_CO2 += co2_tree
        species_CO2[tree['species']]['total'] += co2_tree
        species_CO2[tree['species']]['count'] += 1

    # --- Update Grass Simulation ---
    for cell in grass_cells:
        # If cell is in normal state, there is a chance it begins grazing
        if cell['state'] == 'normal':
            if np.random.rand() < grass_grazing_prob:
                cell['state'] = 'grazed'
                cell['grazing_end'] = t + np.random.uniform(2, 5)
            else:
                cell['height'] = min(grass_max_height, cell['height'] + grass_growth_rate * dt)
        elif cell['state'] == 'grazed':
            if t >= cell['grazing_end']:
                cell['state'] = 'normal'
                cell['height'] = grass_grazed_height  # Reset height after grazing
            else:
                cell['height'] = grass_grazed_height

        # Plot grass cell as a small marker above the terrain
        z_grass = terrain_elevation(cell['x'], cell['y']) + cell['height'] * 0.5
        color = "limegreen" if cell['state'] == 'normal' else "olive"
        ax1.scatter(cell['x'], cell['y'], z_grass, color=color, s=cell['height']*50)

    # --- 2D Plot: CO₂ Sequestration and Species Stats ---
    co2_history.append(total_CO2)
    ax2.set_title("CO₂ Sequestration & Species Stats")
    ax2.set_xlabel("Time (years)")
    ax2.set_ylabel("Total CO₂ Sequestered (kg)")
    ax2.set_xlim(0, years)
    ax2.set_ylim(0, max(co2_history)*1.1 if co2_history else 1e5)
    time_history = np.arange(0, t + dt, dt)
    ax2.plot(time_history, co2_history, color="blue", lw=2)
    ax2.scatter(t, total_CO2, color="red", s=50)
    
    # Build species info text
    species_text = ""
    for sp in species_list:
        count = species_CO2[sp]['count']
        tot = species_CO2[sp]['total']
        avg = tot/count if count > 0 else 0
        species_text += f"{sp}: {count} trees, {avg:,.1f} kg CO₂/tree, {tot:,.1f} kg total\n"
    ax2.text(0.05, 0.95, species_text, transform=ax2.transAxes,
             fontsize=10, verticalalignment='top',
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.7))
    
    # Increment simulation time
    current_year += dt

# =============================
# Create and Run Animation
# =============================
# We'll run the animation for a large number of frames.
anim = FuncAnimation(fig, update, frames=np.arange(0, 1000), interval=200, repeat=False)

plt.tight_layout()
plt.show()
