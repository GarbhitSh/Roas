# views.py
import firebase_admin
from firebase_admin import credentials, firestore

import osmnx as ox
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.distance import great_circle
from django.shortcuts import render
from .forms import RouteForm
from .models import Stop, TravelRoute, TransitStop  
from .f import data
import requests
import numpy as np
from .rf import mrt  

if not firebase_admin._apps:
    cred = credentials.Certificate('D:\\sih\\web dashboard\\roas\\static\\a.json')  

db = firestore.client(app=firebase_admin.get_app(name='view_app'))

geolocator = Nominatim(user_agent="bus_stop_locator")

def get_location(place_name):
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"Could not find location for {place_name}")

def haversine_distance(point1, point2):
    return great_circle(point1, point2).kilometers

def find_nearest_stops(point_A, point_B):
    location = "Delhi, India"

    stops = ox.features_from_place(location, tags={'highway': 'bus_stop'})

    stops = stops[stops.geometry.type == 'Point']

    stop_data = []
    for idx, row in stops.iterrows():
        name = row.get('name', 'Unknown')  
        stop_data.append({
            'name': name,
            'lat': row.geometry.y,
            'lng': row.geometry.x
        })

    df = pd.DataFrame(stop_data)

    # Calculate the distance of each stop from point A and point B
    df['distance_to_a'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_A), axis=1)
    df['distance_to_b'] = df.apply(lambda row: haversine_distance((row['lat'], row['lng']), point_B), axis=1)

    # Find nearest stops to points A and B
    nearest_to_a = df.loc[df['distance_to_a'].idxmin()]
    nearest_to_b = df.loc[df['distance_to_b'].idxmin()]

    return (nearest_to_a['lat'], nearest_to_a['lng']), (nearest_to_b['lat'], nearest_to_b['lng'])

def get_in_between_bus_stops(point_A, point_B):
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

    print(bus_stops_list)
    data(point_A, point_B)
    
    return bus_stops_list

def get_here_route(start_coords, end_coords):
    """
    Fetch the fastest route using HERE Maps API without the 'traffic' parameter.
    """
    api_key = '1GVcX7FwWkZuo606SxV05QyyXp6ADz7Vs93A8I16xz8'  # Replace with your actual HERE API key
    url = f'https://router.hereapi.com/v8/routes?transportMode=car&origin={start_coords[0]},{start_coords[1]}&destination={end_coords[0]},{end_coords[1]}&return=summary,polyline,travelSummary&apiKey={api_key}'

    try:
        response = requests.get(url)
        response.raise_for_status()

        print(f"Request URL: {url}")  # Debug
        print(f"HERE Maps Response: {response.text}")  # Debug

        data = response.json()

        if 'routes' in data and data['routes']:
            route = data['routes'][0]['sections'][0]['summary']
            polyline = data['routes'][0]['sections'][0]['polyline']
            return route, polyline
        else:
            print(f"No route data found for coordinates: {start_coords} to {end_coords}")
            return None, None
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None, None
    except ValueError as json_err:
        print(f"JSON decode error: {json_err} - Response content: {response.text}")
        return None, None

def route_view(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            # Get user input for points A and B
            point_a_name = form.cleaned_data['start_stop']
            point_b_name = form.cleaned_data['end_stop']

            try:
                # Convert place names to geolocation data
                point_A = get_location(point_a_name)
                point_B = get_location(point_b_name)
                
                print(f"Coordinates for Place A ({point_a_name}): {point_A}")
                print(f"Coordinates for Place B ({point_b_name}): {point_B}")

                # Find nearest stops to point A and point B
                start_stop_coords, end_stop_coords = find_nearest_stops(point_A, point_B)

                print(f"Nearest stop to Place A: {start_stop_coords}")
                print(f"Nearest stop to Place B: {end_stop_coords}")

                # Use HERE Maps Routing API to get the route
                route, polyline = get_here_route(start_stop_coords, end_stop_coords)

                if not route or not polyline:
                    error_message = "Unable to calculate the route. Please try again later."
                    return render(request, 'scheduler.html', {'form': form, 'error_message': error_message})

                # Calculate the length in kilometers
                route_length_km = route['length'] / 1000 if route else None

                # Find bus stops in between A and B
                bus_stops_list = get_in_between_bus_stops(point_A, point_B)

                # Call the mrt function to assign the best combination
                best_combination = mrt()

                if best_combination is None:
                    error_message = "No suitable combination found."
                    return render(request, 'scheduler.html', {'form': form, 'error_message': error_message})

                # Update Firebase with the assigned route for the driver app
                route_details = {
                    'start_coords': start_stop_coords,
                    'end_coords': end_stop_coords,
                    'polyline': polyline,
                    'bus_id': best_combination['Bus_ID'],
                    'driver_id': best_combination['Driver_ID'],
                    'conductor_id': best_combination['Conductor_ID']
                }

                db.collection('Routes').document(best_combination['Bus_ID']).set(route_details)

                # Render the route with the map, bus stops, and assignment details
                return render(request, 'scheduler.html', {
                    'form': form,
                    'route': route,
                    'polyline': polyline,
                    'start_coords': start_stop_coords,
                    'end_coords': end_stop_coords,
                    'route_length_km': route_length_km,
                    'bus_stops_list': bus_stops_list,
                    'assigned_bus_id': best_combination['Bus_ID'],
                    'assigned_driver_id': best_combination['Driver_ID'],
                    'assigned_conductor_id': best_combination['Conductor_ID']
                })

            except Exception as e:
                error_message = str(e)
                return render(request, 'scheduler.html', {'form': form, 'error_message': error_message})
    else:
        form = RouteForm()

    return render(request, 'scheduler.html', {'form': form})
