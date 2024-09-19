# mapapp/utils.py

import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
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

def generate_map_image(place_a, place_b):
    point_A = get_location(place_a)
    point_B = get_location(place_b)

    location = "Delhi, India"

    # Fetch bus stops once
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

    # Calculate stops near the route and in between A and B
    def distance_from_line(lat, lng):
        d_ap = haversine_distance(point_A, (lat, lng))
        d_bp = haversine_distance(point_B, (lat, lng))
        s = (d_ab + d_ap + d_bp) / 2
        area = np.sqrt(s * (s - d_ab) * (s - d_ap) * (s - d_bp))
        return (2 * area) / d_ab

    df['distance_from_route'] = df.apply(lambda row: distance_from_line(row['lat'], row['lng']), axis=1)
    nearby_stops = df[df['distance_from_route'] <= 1.0]
    in_between_stops = df[np.abs(df['total_distance'] - d_ab) <= 1.0]

    # Save in_between_stops to database using Django ORM
    bus_stop_objects = [
        BusStop(
            name=row['name'],
            lat=row['lat'],
            lng=row['lng'],
            distance_to_a=row['distance_to_a'],
            distance_to_b=row['distance_to_b'],
            distance_from_route=row['distance_from_route']
        ) for index, row in in_between_stops.iterrows()
    ]
    BusStop.objects.bulk_create(bus_stop_objects)  # Bulk insert for efficiency

    # Get the graph and shortest path
    G = ox.graph_from_place(location, network_type='drive')
    origin_node = ox.nearest_nodes(G, point_A[1], point_A[0])
    destination_node = ox.nearest_nodes(G, point_B[1], point_B[0])
    route = nx.shortest_path(G, origin_node, destination_node, weight='length')

    # Plot
    fig, ax = ox.plot_graph_route(G, route, route_linewidth=6, node_size=0, bgcolor='w', show=False, close=False)
    ax.scatter(df['lng'], df['lat'], c='gray', alpha=0.5, label='All Bus Stops')
    ax.scatter(nearby_stops['lng'], nearby_stops['lat'], c='blue', label='Stops Near Route')
    ax.scatter(in_between_stops['lng'], in_between_stops['lat'], c='green', label='Stops Between A and B')
    ax.scatter([point_A[1], point_B[1]], [point_A[0], point_B[0]], c='red', marker='X', s=100, label='Points A and B')
    print(nearby_stops['lng'], nearby_stops['lat'])
    lat_min, lat_max = min(point_A[0], point_B[0]) - 0.01, max(point_A[0], point_B[0]) + 0.01
    lon_min, lon_max = min(point_A[1], point_B[1]) - 0.01, max(point_A[1], point_B[1]) + 0.01
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    plt.title(f'Bus Stops Near Route and Between {place_a} and {place_b}')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    map_image = base64.b64encode(image_png).decode('utf-8')
    plt.close()
    
    return map_image
