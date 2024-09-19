import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import numpy as np
from .models import BusStop  # Import the Django model

# Initialize geolocator
geolocator = Nominatim(user_agent="bus_stop_locator")

def get_location(place_name):
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find location for {place_name}")

def haversine_distance(point1, point2):
    return great_circle(point1, point2).kilometers

def get_in_between_bus_stops(place_a, place_b):
    # Get coordinates for place A and place B
    point_A = get_location(place_a)
    point_B = get_location(place_b)

    location = "Delhi, India"

    # Fetch bus stops
    bus_stops = ox.features_from_place(location, tags={'highway': 'bus_stop'})
    bus_stops = bus_stops[bus_stops.geometry.type == 'Point']

    bus_stop_data = [
        {'name': row.get('name', 'Unknown'), 'lat': row.geometry.y, 'lng': row.geometry.x}
        for idx, row in bus_stops.iterrows()
    ]
    df = pd.DataFrame(bus_stop_data)

    # Precompute distances to reduce redundant calculations
    d_ab = haversine_distance(point_A, point_B)
    df['distance_to_a'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_A), axis=1)
    df['distance_to_b'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_B), axis=1)
    df['total_distance'] = df['distance_to_a'] + df['distance_to_b']

    # Calculate stops in between A and B
    def distance_from_line(lat, lng):
        d_ap = haversine_distance(point_A, (lat, lng))
        d_bp = haversine_distance(point_B, (lat, lng))
        s = (d_ab + d_ap + d_bp) / 2
        area = np.sqrt(s * (s - d_ab) * (s - d_ap) * (s - d_bp))
        return (2 * area) / d_ab

    df['distance_from_route'] = df.apply(lambda row: distance_from_line(row['lat'], row['lng']), axis=1)
    in_between_stops = df[np.abs(df['total_distance'] - d_ab) <= 1.0]

    # Create list of bus stops and their coordinates
    bus_stops_list = in_between_stops[['name', 'lat', 'lng']].to_dict(orient='records')

    return bus_stops_list
