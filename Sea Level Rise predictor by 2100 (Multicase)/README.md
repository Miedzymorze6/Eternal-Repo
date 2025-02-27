[![Downloads](https://static.pepy.tech/badge/sea-level-simulation)](https://pepy.tech/project/sea-level-simulation)

# Sea Level Rise Simulation

This project simulates sea level rise over time using elevation data retrieved from the SRTM database. It generates an animated GIF showing different climate scenarios and their effects on land submersion.

## Features
- Fetches elevation data dynamically
- Simulates sea level rise under different emission scenarios
- Generates an animated visualization of affected areas

## Installation

```bash
pip install numpy srtm matplotlib imageio
```

## Usage

```python
import numpy as np
import srtm
import matplotlib.pyplot as plt
import imageio
from io import BytesIO

# Define the region of interest
lat_min, lat_max = 36.5, 47.0
lon_min, lon_max = 6.5, 18.5
num_lat, num_lon = 1000, 800
lats = np.linspace(lat_min, lat_max, num_lat)
lons = np.linspace(lon_min, lon_max, num_lon)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# Retrieve DEM (elevation) Data Using SRTM
elevation_data = srtm.get_data()
elevation_grid = np.zeros((num_lat, num_lon))
for i in range(num_lat):
    for j in range(num_lon):
        elev = elevation_data.get_elevation(lat_grid[i, j], lon_grid[i, j])
        elevation_grid[i, j] = elev if elev is not None else 0

# Define scenarios
years = np.arange(2025, 2101, 5)
target_rises = {
    'Stable Emissions': 1.5,
    'Zero Emissions': 0.6,
    'High Emissions': 3.75
}
scenarios = list(target_rises.keys())

# Generate animated GIF
frames = []
for year in years:
    fig, axes = plt.subplots(1, 3, figsize=(18, 10), dpi=120)
    for ax, scenario in zip(axes, scenarios):
        target = target_rises[scenario]
        time_elapsed = year - 2025
        sea_level = target * (time_elapsed / (2100 - 2025)) ** 2
        flooded_mask = elevation_grid < sea_level
        ax.imshow(elevation_grid, cmap='terrain', origin='upper', extent=[lon_min, lon_max, lat_min, lat_max])
        grey_overlay = np.zeros((num_lat, num_lon, 4))
        grey_overlay[..., :3] = 0.8
        grey_overlay[..., 3] = np.where(flooded_mask, 1, 0)
        ax.imshow(grey_overlay, origin='upper', extent=[lon_min, lon_max, lat_min, lat_max])
        ax.set_title(f"{scenario}\nYear {year} - Sea Level: {sea_level:.2f} m")
        ax.axis('off')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)
    frames.append(imageio.imread(buf))

# Save the animated GIF
output_filename = 'sea_level_rise.gif'
imageio.mimsave(output_filename, frames, duration=0.5)
print(f"GIF saved as '{output_filename}'.")
```

## Output
- Generates `sea_level_rise.gif` showing the progressive impact of rising sea levels under different climate scenarios.
