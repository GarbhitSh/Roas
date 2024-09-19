# roas/urls.py

from django.urls import path, include
from .views import route_view

urlpatterns = [
    
    path('rop',route_view, name='staff'),


]
