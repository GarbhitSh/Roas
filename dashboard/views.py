# dashboard/views.py

from django.shortcuts import render
import firebase_admin
from django.shortcuts import render
from .utils import generate_map_image
from firebase_admin import credentials, firestore

# Use a service account
cred = credentials.Certificate('D:\\sih\\web dashboard\\roas\\dashboard\\a.json')
firebase_admin.initialize_app(cred)

db = firestore.client()


def index(request):
    return render(request, 'index.html')

def buses(request):
    return render(request, 'buses.html')

def drivers(request):
    drivers_ref = db.collection('DriverDetails')
    # Fetch all documents in the collection
    drivers = drivers_ref.stream()

    driver_list = []
    for driver in drivers:
        driver_data = driver.to_dict()
        driver_data['id'] = driver.id  # Add the document ID to the data
        driver_list.append(driver_data)

    return render(request, 'drivers.html', {'drivers': driver_list})
    

def emergency(request):
    return render(request, 'emergency.html')


    

def scheduler(request):
    return render(request, 'scheduler.html')

def staff(request):
    return render(request, 'staff.html')
def emergencyResponse(request):
    return render(request, 'emergencyResponse.html')



def routes(request):
    map_image = None
    error = None

    if request.method == 'POST':
        place_a = request.POST.get('place_a')
        place_b = request.POST.get('place_b')

        try:
            map_image = generate_map_image(place_a, place_b)
        except ValueError as e:
            error = str(e)
    
    return render(request, 'routes.html', {'map_image': map_image, 'error': error})
