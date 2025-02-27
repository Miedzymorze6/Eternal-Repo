import numpy as np
import srtm
import matplotlib.pyplot as plt
import imageio
from io import BytesIO

# ----- Define the Italy region -----
lat_min, lat_max = 36.5, 47.0  # Covers entire Italy
lon_min, lon_max = 6.5, 18.5  

num_lat, num_lon = 1000, 800  # Increased resolution for clarity
lats = np.linspace(lat_min, lat_max, num_lat)
lons = np.linspace(lon_min, lon_max, num_lon)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# ----- Retrieve DEM (elevation) Data Using SRTM -----
print("Fetching elevation data from SRTM. This may take some time...")
elevation_data = srtm.get_data()
elevation_grid = np.zeros((num_lat, num_lon))

for i in range(num_lat):
    for j in range(num_lon):
        elev = elevation_data.get_elevation(lat_grid[i, j], lon_grid[i, j])
        elevation_grid[i, j] = elev if elev is not None else 0  # Default to 0 if no data

print("Elevation data fetched.")

# ----- Sea Level Rise Parameters -----
years = np.arange(2025, 2101, 5)  # 5-year increments from 2025 to 2100
T = 2100 - 2025  # 75-year period

# Target sea level rise scenarios (meters by 2100)
target_rises = {
    'Stable Emissions': 1.5,
    'Zero Emissions': 0.6,
    'High Emissions': 3.75
}
scenarios = list(target_rises.keys())

# ----- Generate Frames for the Animated GIF -----
frames = []
for year in years:
    fig, axes = plt.subplots(1, 3, figsize=(18, 10), dpi=120)  # Adjusted aspect ratio
    
    for ax, scenario in zip(axes, scenarios):
        target = target_rises[scenario]
        time_elapsed = year - 2025
        sea_level = target * (time_elapsed / T) ** 2
        
        # Determine flooded areas
        flooded_mask = elevation_grid < sea_level

        # Plot the terrain
        ax.imshow(elevation_grid, cmap='terrain', origin='upper',
                  extent=[lon_min, lon_max, lat_min, lat_max], aspect='auto')

        # Create a light grey overlay (RGB: 0.8, 0.8, 0.8) for flooded areas
        grey_overlay = np.zeros((num_lat, num_lon, 4))
        grey_overlay[..., :3] = 0.8  # Grey color
        grey_overlay[..., 3] = np.where(flooded_mask, 1, 0)  # Fully opaque if flooded
        
        ax.imshow(grey_overlay, origin='upper',
                  extent=[lon_min, lon_max, lat_min, lat_max], aspect='auto')

        # Add a title with the scenario, year, and sea level rise
        ax.set_title(f"{scenario}\nYear {year} - Sea Level: {sea_level:.2f} m", fontsize=14)
        ax.axis('off')

    plt.tight_layout()

    # Save the current frame to an in-memory buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    frame = imageio.imread(buf)
    frames.append(frame)

# ----- Create and Save the Animated GIF -----
output_filename = 'italy_sea_level_rise.gif'
imageio.mimsave(output_filename, frames, duration=0.5)
print(f"GIF saved as '{output_filename}'.")
