**EV Charging Station Placement Optimization**

**Overview**
This project optimizes the placement of electric vehicle (EV) charging stations in a given city using geospatial data, multi-criteria scoring, and integer linear programming (ILP). The goal is to maximize accessibility by considering factors such as:

Proximity to downtown (centrality)
Distance from major roads
Population density
Business/commercial centers
The solution selects the best K locations while ensuring a minimum distance between stations.

**Features**
✅ Download and process road network data using OSMnx (Poznan used as a reference)
✅ Compute candidate locations and evaluate site suitability
✅ Optimize station placement using ILP (PuLP)
✅ Visualize results with Folium on an interactive map

**How It Works**

1. Data Collection & Candidate Extraction
Downloads road network data for a specified city (default: Poznań, Poland)
Samples 500 random candidate locations from the network
2. Score Computation
Each candidate location is evaluated based on:
✔ Centrality: Closer to downtown = higher score
✔ Road Proximity: Near major roads = higher score
✔ Population Density: Closer to high-population areas = higher score
✔ Business Centers: Near commercial hubs = higher score

3. Optimization using Integer Linear Programming (ILP)
Selects K optimal locations
Ensures a minimum distance (D_min) constraint between stations
4. Visualization
Generates an interactive Folium map with:
⚪ Candidate locations (gray)
🔴 Selected optimal charging stations (red)
Running the Script

**Final Steps**

After execution, the optimized station placements will be saved in:
✅ ev_stations_map.html (interactive visualization)
