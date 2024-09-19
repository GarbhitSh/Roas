import osmnx as ox
import pandas as pd
from shapely.geometry import Point
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
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

def data (point_A, point_B):

# Define the area of interest (Delhi, India)
    location = "Delhi, India"

# Fetch bus stops using the updated function
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
    distance_threshold = 1.0  # in kilometers; adjust as needed
    df['distance_from_route'] = df.apply(lambda row: distance_from_line(row['lat'], row['lng'], point_A, point_B), axis=1)
    nearby_stops = df[df['distance_from_route'] <= distance_threshold]

# Filter bus stops that are directly between A and B
    df['distance_to_a'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_A), axis=1)
    df['distance_to_b'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_B), axis=1)

# Bus stops that are between A and B: distance to A + distance to B should be approximately equal to the distance between A and B
    distance_between_a_b = haversine_distance(point_A, point_B)
    in_between_stops = df[np.abs(df['distance_to_a'] + df['distance_to_b'] - distance_between_a_b) <= distance_threshold]




    print(in_between_stops)
    print(nearby_stops)



# Assuming `nearby_stops` is your DataFrame with the filtered bus stop data
    in_between_stops.to_json('D:\\sih\\web dashboard\\roas\\static\\json\\in_between_stops.json', orient='records')


# Calculate the distance of each bus stop from the straight line connecting A and B
def distance_from_line(lat, lng, point_A, point_B):
    d_ab = haversine_distance(point_A, point_B)
    d_ap = haversine_distance(point_A, (lat, lng))
    d_bp = haversine_distance(point_B, (lat, lng))
    s = (d_ab + d_ap + d_bp) / 2
    area = np.sqrt(s * (s - d_ab) * (s - d_ap) * (s - d_bp))
    return (2 * area) / d_ab

# Filter bus stops that are near the route between A and B
