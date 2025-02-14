import osmnx as ox
import numpy as np
import pandas as pd
import folium
from pulp import LpProblem, LpMaximize, LpVariable, LpBinary
from shapely.geometry import Point
import random

# -----------------------------
# Utility: Haversine Distance
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    from math import radians, sin, cos, sqrt, atan2
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a)) 
    km = 6371 * c
    return km

# -----------------------------
# 1. Data Collection & Candidate Extraction
# -----------------------------
place_name = "Poznan, Poland"
print("Downloading road network for", place_name)
graph = ox.graph_from_place(place_name, network_type='drive')
nodes, edges = ox.graph_to_gdfs(graph)

# For reproducibility, set a fixed seed and sample candidate nodes
np.random.seed(random.randint(1,100))
candidate_nodes = nodes[['y', 'x']].sample(n=500, random_state=42).reset_index(drop=True)
candidate_nodes.columns = ['lat', 'lon']
print(f"Selected {len(candidate_nodes)} candidate locations.")

# -----------------------------
# 2. Compute Factor Scores for Each Candidate
# -----------------------------
# Define weights for each factor (must sum to 1.0)
w_centrality = 0.40  # proximity to downtown
w_road       = 0.35  # proximity to major roads
w_population = 0.20  # proximity to high-population areas
w_business   = 0.10  # proximity to business/commercial centers

# Define downtown (central reference) for Poznan
downtown = (52.40937554, 16.9214994)

# --- Centrality Factor (Downtown Proximity) ---
def centrality_score(lat, lon, downtown, max_dist):
    d = haversine(lat, lon, downtown[0], downtown[1])
    # Closer to downtown gives a higher score (normalized between 0 and 1)
    return max(0, 1 - d / max_dist)

# Compute distance to downtown for each candidate
candidate_nodes['dist_to_downtown'] = candidate_nodes.apply(
    lambda row: haversine(row['lat'], row['lon'], downtown[0], downtown[1]), axis=1)
max_dist = candidate_nodes['dist_to_downtown'].max()

candidate_nodes['centrality'] = candidate_nodes.apply(
    lambda row: centrality_score(row['lat'], row['lon'], downtown, max_dist), axis=1)

# --- Road Proximity Factor ---
# Define major road types
major_road_types = ['motorway', 'trunk', 'primary', 'secondary']
def is_major(highway):
    if isinstance(highway, list):
        return any(r in major_road_types for r in highway)
    else:
        return highway in major_road_types

# Filter edges with geometry and are major roads
edges = edges[edges['highway'].notnull()]
major_edges = edges[edges['highway'].apply(is_major)]
print(f"Found {len(major_edges)} major road segments.")

# Compute minimum distance from candidate to any major road
def min_distance_to_roads(lat, lon, road_geometries):
    point = Point(lon, lat)  # shapely expects (lon, lat)
    distances = [point.distance(road) for road in road_geometries]
    # Approximate conversion: 1 degree ~ 111 km (suitable for small distances)
    if distances:
        return min(distances) * 111  
    else:
        return np.inf

road_geoms = major_edges['geometry'].tolist()
candidate_nodes['dist_to_road'] = candidate_nodes.apply(
    lambda row: min_distance_to_roads(row['lat'], row['lon'], road_geoms), axis=1)

# Define threshold for being “close” to a major road (in km)
road_threshold = 0.5
candidate_nodes['road_factor'] = candidate_nodes['dist_to_road'].apply(
    lambda d: max(0, 1 - d / road_threshold) if d < road_threshold else 0)

# --- Population Density Factor ---
# Define example high-population centers (these should be based on actual data if available)
population_centers = [(52.389880, 16.962277), (52.4073535,17.0576333), (52.3918581,16.8953774)]
pop_threshold = 3.0  # km threshold

def population_factor(lat, lon):
    distances = [haversine(lat, lon, pc[0], pc[1]) for pc in population_centers]
    d_min = min(distances)
    return max(0, 1 - d_min / pop_threshold)

candidate_nodes['pop_factor'] = candidate_nodes.apply(
    lambda row: population_factor(row['lat'], row['lon']), axis=1)

# --- Business/Commercial Density Factor ---
# Define example business centers (these should be based on actual data if available)
business_centers = [(52.40937554, 16.9214994), (52.387838,16.8754466), (52.3584619,16.8340429)]
business_threshold = 2.0  # km threshold

def business_factor(lat, lon):
    distances = [haversine(lat, lon, bc[0], bc[1]) for bc in business_centers]
    d_min = min(distances)
    return max(0, 1 - d_min / business_threshold)

candidate_nodes['business_factor'] = candidate_nodes.apply(
    lambda row: business_factor(row['lat'], row['lon']), axis=1)

# --- Final Combined Score ---
candidate_nodes['score'] = (w_centrality * candidate_nodes['centrality'] +
                            w_road * candidate_nodes['road_factor'] +
                            w_population * candidate_nodes['pop_factor'] +
                            w_business * candidate_nodes['business_factor'])

print("\nSample candidate scores:")
print(candidate_nodes[['lat', 'lon', 'centrality', 'road_factor', 
                        'pop_factor', 'business_factor', 'score']].head())

# -----------------------------
# 3. Facility Location Optimization with ILP
# -----------------------------
# Parameters for optimization
K = 6               # number of stations to select
D_min = 5         # minimum allowed distance between any two selected stations (km)
# (Adjust D_min according to local city density)

# Create the ILP problem
prob = LpProblem("EV_Charging_Station_Placement", LpMaximize)

num_candidates = len(candidate_nodes)
x_vars = [LpVariable(f"x_{i}", cat=LpBinary) for i in range(num_candidates)]

# Objective: maximize the total weighted score
scores = candidate_nodes['score'].tolist()
prob += sum(scores[i] * x_vars[i] for i in range(num_candidates)), "Total_Profit_Score"

# Constraint: Exactly K stations must be selected
prob += sum(x_vars) == K, "Total_Stations"

# Constraint: Enforce minimum distance between any two selected sites
coords = candidate_nodes[['lat', 'lon']].values
for i in range(num_candidates):
    for j in range(i + 1, num_candidates):
        d = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
        if d < D_min:
            prob += x_vars[i] + x_vars[j] <= 1, f"min_dist_constraint_{i}_{j}"

print("\nSolving optimization problem...")
status = prob.solve()
print(f"Solver status: {prob.status}")

# Retrieve selected candidate indices
selected_indices = [i for i in range(num_candidates) if x_vars[i].varValue == 1]
selected_sites = candidate_nodes.iloc[selected_indices][['lat', 'lon', 'score']]
print("\nSelected EV Charging Station Locations:")
print(selected_sites)

# -----------------------------
# 4. Visualization with Folium
# -----------------------------
m = folium.Map(location=[downtown[0], downtown[1]], zoom_start=13)

# Add all candidate locations as gray circles with popups showing their score
for idx, row in candidate_nodes.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=3,
        color="gray",
        fill=True,
        fill_color="gray",
        fill_opacity=0.6,
        popup=f"Score: {row['score']:.2f}"
    ).add_to(m)

# Highlight selected stations with red markers and popups showing their score
for idx, row in selected_sites.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"Score: {row['score']:.2f}",
        icon=folium.Icon(color="red", icon="flash")
    ).add_to(m)

m.save("ev_stations_map.html")
print("\nMap saved as 'ev_stations_map.html'.")
