import osmnx as ox
import pandas as pd
from shapely.geometry import Point, LineString
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# Initialize geolocator
geolocator = Nominatim(user_agent="bus_stop_locator")

# Function to get geolocation data from a place name
def get_location(place_name):
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find location for {place_name}")

# Function to calculate the distance between two points
def haversine_distance(point1, point2):
    return great_circle(point1, point2).kilometers

# Get user input for points A and B
point_a_name = input("Enter the name of Place A: ")
point_b_name = input("Enter the name of Place B: ")

# Convert place names to geolocation data
point_A = get_location(point_a_name)
point_B = get_location(point_b_name)

print(f"Coordinates for Place A ({point_a_name}): {point_A}")
print(f"Coordinates for Place B ({point_b_name}): {point_B}")

# Define the area of interest (Delhi, India)
location = "Delhi, India"

# Fetch bus stops using osmnx
bus_stops = ox.features_from_place(location, tags={'highway': 'bus_stop'})

# Filter only Point geometries (bus stops should be points, not polygons)
bus_stops = bus_stops[bus_stops.geometry.type == 'Point']

# Extract relevant data: name, latitude, longitude
bus_stop_data = []
for idx, row in bus_stops.iterrows():
    name = row.get('name', 'Unknown')  # Safely get the name or default to 'Unknown'
    bus_stop_data.append({
        'name': name,
        'lat': row.geometry.y,
        'lng': row.geometry.x
    })

# Convert to DataFrame
df = pd.DataFrame(bus_stop_data)

# Calculate the distance of each bus stop from the straight line connecting A and B
def distance_from_line(lat, lng, point_A, point_B):
    d_ab = haversine_distance(point_A, point_B)
    d_ap = haversine_distance(point_A, (lat, lng))
    d_bp = haversine_distance(point_B, (lat, lng))
    s = (d_ab + d_ap + d_bp) / 2
    area = np.sqrt(s * (s - d_ab) * (s - d_ap) * (s - d_bp))
    return (2 * area) / d_ab

# Filter bus stops that are near the route between A and B
distance_threshold = 1.0  # in kilometers; adjust as needed
df['distance_from_route'] = df.apply(lambda row: distance_from_line(row['lat'], row['lng'], point_A, point_B), axis=1)
nearby_stops = df[df['distance_from_route'] <= distance_threshold]

# Filter bus stops that are directly between A and B
df['distance_to_a'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_A), axis=1)
df['distance_to_b'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_B), axis=1)

# Bus stops that are between A and B: distance to A + distance to B should be approximately equal to the distance between A and B
distance_between_a_b = haversine_distance(point_A, point_B)
in_between_stops = df[np.abs(df['distance_to_a'] + df['distance_to_b'] - distance_between_a_b) <= distance_threshold]

# Fetch the street network graph for the area of interest
G = ox.graph_from_place(location, network_type='drive')

# Find the nearest nodes to points A and B in the network
origin_node = ox.nearest_nodes(G, point_A[1], point_A[0])
destination_node = ox.nearest_nodes(G, point_B[1], point_B[0])

# Calculate the shortest path between A and B using Dijkstra's algorithm
route = nx.shortest_path(G, origin_node, destination_node, weight='length')

# Plot the route with bus stops
fig, ax = ox.plot_graph_route(G, route, route_linewidth=6, node_size=0, bgcolor='w', show=False, close=False)
plt.scatter(df['lng'], df['lat'], c='gray', alpha=0.5, label='All Bus Stops')
plt.scatter(nearby_stops['lng'], nearby_stops['lat'], c='blue', label='Stops Near Route')
plt.scatter(in_between_stops['lng'], in_between_stops['lat'], c='green', label='Stops Between A and B')
plt.scatter([point_A[1], point_B[1]], [point_A[0], point_B[0]], c='red', marker='X', s=100, label='Points A and B')
plt.title(f'Bus Stops Near Route and Between {point_a_name} and {point_b_name}')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.legend()
plt.show()

# Save the nearby stops and in-between stops to separate Excel files
nearby_file = 'nearby_bus_stops.xlsx'
in_between_file = 'in_between_bus_stops.xlsx'
nearby_stops.to_excel(nearby_file, index=False)
in_between_stops.to_excel(in_between_file, index=False)

print(in_between_stops)
print(nearby_stops)
print(f"Nearby bus stops saved to {nearby_file}")
print(f"In-between bus stops saved to {in_between_file}")
