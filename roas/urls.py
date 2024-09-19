# roas/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Routeop.urls')),  # Include the dashboard app's URLs
    path('', include('dashboard.urls')),  # Include the dashboard app's URLs
   
]
