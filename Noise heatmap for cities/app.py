import osmnx as ox
import folium
import geopandas as gpd
import random
from shapely.geometry import Point
from shapely.ops import transform
from pyproj import Transformer
from folium.plugins import HeatMap

# --------- Helper Function to Generate Random Points ---------
def generate_random_points_in_polygon(polygon, num_points):
    """Generate random points within a given polygon."""
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < num_points:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(p):
            points.append(p)
    return points

# --------- Define Place and Download Base Data ---------
place_name = 'Riga, Latvia'

print("Downloading Latvia boundary...")
gdf_latvia = ox.geocode_to_gdf(place_name)
latvia_polygon = gdf_latvia.iloc[0].geometry

print("Downloading road network (this may take a while)...")
G = ox.graph_from_place(place_name, network_type='drive')
gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
roads_union = gdf_edges.unary_union  # Combine road geometries

print("Downloading industrial zones...")
industrial_tags = {'landuse': 'industrial'}
industrial_gdf = ox.features_from_place(place_name, tags=industrial_tags)
industrial_polygons = industrial_gdf[industrial_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
industrial_union = industrial_polygons.unary_union if not industrial_polygons.empty else None

print("Downloading airports...")
airport_tags = {'aeroway': 'aerodrome'}
airport_gdf = ox.features_from_place(place_name, tags=airport_tags)
airport_polygons = airport_gdf[airport_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
airport_union = airport_polygons.unary_union if not airport_polygons.empty else None

print("Downloading parks...")
park_tags = {'leisure': 'park'}
park_gdf = ox.features_from_place(place_name, tags=park_tags)
park_polygons = park_gdf[park_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
park_union = park_polygons.unary_union if not park_polygons.empty else None

print("Downloading railways...")
railway_tags = {'railway': 'rail'}
railway_gdf = ox.features_from_place(place_name, tags=railway_tags)
railway_union = railway_gdf.unary_union if not railway_gdf.empty else None

print("Downloading commercial zones...")
commercial_tags = {'landuse': 'commercial'}
commercial_gdf = ox.features_from_place(place_name, tags=commercial_tags)
commercial_polygons = commercial_gdf[commercial_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
commercial_union = commercial_polygons.unary_union if not commercial_polygons.empty else None

print("Downloading water bodies...")
water_tags = {'natural': 'water'}
water_gdf = ox.features_from_place(place_name, tags=water_tags)
water_polygons = water_gdf[water_gdf.geometry.type.isin(['Polygon', 'MultiPolygon'])]
water_union = water_polygons.unary_union if not water_polygons.empty else None

# --------- Prepare for Distance Calculations (Project Geometries) ---------
# Define a transformer from EPSG:4326 (lat/lon) to EPSG:3857 (meters)
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
def project_geom(geom):
    return transform(transformer.transform, geom)

roads_union_proj = project_geom(roads_union)
industrial_union_proj = project_geom(industrial_union) if industrial_union else None
airport_union_proj = project_geom(airport_union) if airport_union else None
park_union_proj = project_geom(park_union) if park_union else None
railway_union_proj = project_geom(railway_union) if railway_union else None
commercial_union_proj = project_geom(commercial_union) if commercial_union else None
water_union_proj = project_geom(water_union) if water_union else None

# --------- Generate Sample Points and Simulate Noise Levels ---------
num_points = 500  # Increase for higher resolution if needed
print("Generating random sample points inside Latvia boundary...")
points = generate_random_points_in_polygon(latvia_polygon, num_points)

heat_data = []  # List to hold [lat, lon, intensity] for the heatmap

for pt in points:
    pt_proj = project_geom(pt)
    # Start with a baseline noise level (~55 dB) with some randomness.
    noise = random.gauss(55, 3)
    
    # Industrial zones: if inside, boost noise to ~80 dB.
    if industrial_union_proj and industrial_union_proj.contains(pt_proj):
        noise = max(noise, random.gauss(80, 5))
    
    # Airports: if inside or within 100 m, boost noise to ~90 dB.
    if airport_union_proj:
        if airport_union_proj.contains(pt_proj) or pt_proj.distance(airport_union_proj) < 100:
            noise = max(noise, random.gauss(90, 5))
    
    # Roads: increase noise based on proximity.
    road_dist = pt_proj.distance(roads_union_proj)
    if road_dist < 10:
        noise = max(noise, random.gauss(90, 3))
    elif road_dist < 25:
        noise = max(noise, random.gauss(85, 3))
    elif road_dist < 50:
        noise = max(noise, random.gauss(80, 3))
    elif road_dist < 100:
        noise = max(noise, random.gauss(75, 3))
    
    # Railways: similar thresholds as roads.
    if railway_union_proj:
        railway_dist = pt_proj.distance(railway_union_proj)
        if railway_dist < 10:
            noise = max(noise, random.gauss(88, 3))
        elif railway_dist < 25:
            noise = max(noise, random.gauss(85, 3))
        elif railway_dist < 50:
            noise = max(noise, random.gauss(80, 3))
    
    # Commercial zones: moderate noise boost if inside or near (<50 m).
    if commercial_union_proj:
        if commercial_union_proj.contains(pt_proj) or pt_proj.distance(commercial_union_proj) < 50:
            noise = max(noise, random.gauss(70, 3))
    
    # Parks: reduce noise by 10 dB.
    if park_union_proj and park_union_proj.contains(pt_proj):
        noise = max(50, noise - 10)
    
    # Water bodies: reduce noise by 15 dB.
    if water_union_proj and water_union_proj.contains(pt_proj):
        noise = max(50, noise - 15)
    
    # Normalize noise to an intensity value between 0 and 1.
    # Assumed noise range: 50 dB (quiet) to 90 dB (loud).
    intensity = max(0, min(1, (noise - 50) / 40))
    heat_data.append([pt.y, pt.x, intensity])

# --------- Create the Folium Map with Only the Heatmap Layer ---------
center_lat = gdf_latvia.iloc[0].geometry.centroid.y
center_lon = gdf_latvia.iloc[0].geometry.centroid.x
m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

# Create heatmap (green for quiet, red for noisy)
gradient = {'0.0': 'green', '0.5': 'yellow', '1.0': 'red'}
heatmap = HeatMap(heat_data, radius=10, gradient=gradient)
m.add_child(heatmap)

# --------- Save the Map to HTML ---------
output_file = 'noise_pollution_heatmap_latvia.html'
m.save(output_file)
print(f"Map saved to {output_file}")
