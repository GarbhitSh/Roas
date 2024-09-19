# dashboard/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('buses', views.buses, name='buses'),
    path('drivers', views.drivers, name='drivers'),
    path('emergency', views.emergency, name='emergency'),
    path('routes', views.routes, name='routes'),
    path('scheduler', views.scheduler, name='scheduler'),
    path('staff', views.staff, name='staff'),
    path('emergencyResponse',views.emergencyResponse, name='emergencyResponse'),
]
