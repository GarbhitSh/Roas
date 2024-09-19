# rf.py

import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# Step 1: Initialize Firebase Admin SDK
# Step 1: Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate('D:\\sih\\web dashboard\\roas\\static\\a.json')  # Replace with your service account key file path
    firebase_admin.initialize_app(cred, name='view_app')

# Initialize Firestore
db = firestore.client(app=firebase_admin.get_app(name='view_app'))

def fetch_bus_details():
    buses_ref = db.collection('BusDetails')
    buses = buses_ref.stream()
    bus_data = []

    for bus in buses:
        bus_dict = bus.to_dict()
        bus_dict['Bus_ID'] = bus.id
        bus_data.append(bus_dict)

    return pd.DataFrame(bus_data)

def fetch_driver_details():
    drivers_ref = db.collection('DriverDetails')
    drivers = drivers_ref.stream()
    driver_data = []

    for driver in drivers:
        driver_dict = driver.to_dict()
        driver_dict['Driver_ID'] = driver.id
        driver_data.append(driver_dict)

    return pd.DataFrame(driver_data)

def fetch_conductor_details():
    conductors_ref = db.collection('BusStaffDetails')
    conductors = conductors_ref.stream()
    conductor_data = []

    for conductor in conductors:
        conductor_dict = conductor.to_dict()
        conductor_dict['Conductor_ID'] = conductor.id
        conductor_data.append(conductor_dict)

    return pd.DataFrame(conductor_data)

# Step 4: Data Preparation
def prepare_data(bus_df, driver_df, conductor_df):
    # Debug: Check the column names
    print("Bus DataFrame Columns:", bus_df.columns)
    print("Driver DataFrame Columns:", driver_df.columns)
    print("Conductor DataFrame Columns:", conductor_df.columns)

    # Check if 'status' column exists in all DataFrames
    if 'status' not in bus_df.columns:
        raise KeyError("Column 'status' not found in bus DataFrame")
    if 'status' not in driver_df.columns:
        raise KeyError("Column 'status' not found in driver DataFrame")
    if 'status' not in conductor_df.columns:
        raise KeyError("Column 'status' not found in conductor DataFrame")

    # Filter available entities
    available_buses = bus_df[bus_df['status'].str.lower() == 'available']
    available_drivers = driver_df[driver_df['status'].str.lower() == 'active']
    available_conductors = conductor_df[conductor_df['status'].str.lower() == 'available']

    combined_data = pd.merge(available_buses, available_drivers, how='cross', suffixes=('_bus', '_driver'))
    combined_data = pd.merge(combined_data, available_conductors, how='cross')

    combined_data.rename(columns={'Expirence': 'Experience_driver', 'Years Of Expirience': 'Experience_conductor'}, inplace=True)

    combined_data['Suitability'] = np.where(
        (combined_data['Experience_driver'] > 7) & 
        (combined_data['Experience_conductor'] > 5) & 
        (combined_data['Performance Rating'] > 4), 
        1, 0)

    return combined_data

def train_model(data):
    features = data[['Daily Mileage (km)', 'Seating Capacity', 'Manufacturing Year', 'Experience_driver', 'Experience_conductor', 'Performance Rating']]
    target = data['Suitability']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    # Train a RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    return model

# Step 6: Predict Best Combination and Check Availability
def check_and_assign_best_combination(model, data):
    # Filter for the best combinations based on the trained model
    data['Predicted_Suitability'] = model.predict(data[['Daily Mileage (km)', 'Seating Capacity', 'Manufacturing Year', 'Experience_driver', 'Experience_conductor', 'Performance Rating']])
    best_combinations = data[data['Predicted_Suitability'] == 1]

    # Iterate over sorted best combinations to find the available one
    for _, row in best_combinations.iterrows():
        bus_id = row['Bus_ID']
        driver_id = row['Driver_ID']
        conductor_id = row['Conductor_ID']

        # Check the availability status from Firestore
        bus_status = db.collection('BusDetails').document(bus_id).get().to_dict()['status']
        driver_status = db.collection('DriverDetails').document(driver_id).get().to_dict()['status']
        conductor_status = db.collection('BusStaffDetails').document(conductor_id).get().to_dict()['status']

        if bus_status.lower() == 'available' and driver_status.lower() == 'active' and conductor_status.lower() == 'available':
            # Update statuses in Firestore
            db.collection('BusDetails').document(bus_id).update({'status': 'busy'})
            db.collection('DriverDetails').document(driver_id).update({'status': 'busy'})
            db.collection('BusStaffDetails').document(conductor_id).update({'status': 'busy'})
            
            print(f"Assigned Bus: {bus_id}, Driver: {driver_id}, Conductor: {conductor_id}")
            return row[['Bus_ID', 'Driver_ID', 'Conductor_ID']]
    
    print("No available combination found.")
    return None

# Main function
def mrt():
    # Fetch data from Firebase
    bus_df = fetch_bus_details()
    driver_df = fetch_driver_details()
    conductor_df = fetch_conductor_details()

    # Prepare data
    try:
        combined_data = prepare_data(bus_df, driver_df, conductor_df)
    except KeyError as e:
        print(f"Error: {e}")
        return None

    # Train model
    model = train_model(combined_data)

    # Check and assign the best combination
    best_combination = check_and_assign_best_combination(model, combined_data)

    if best_combination is not None:
        print("Assigned Best Combination of Bus, Driver, and Conductor:")
        print(best_combination)
        return best_combination
    else:
        print("No suitable combination found.")
        return None
