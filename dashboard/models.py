# mapapp/models.py

from django.db import models

class BusStop(models.Model):
    name = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    distance_to_a = models.FloatField()
    distance_to_b = models.FloatField()
    distance_from_route = models.FloatField()

    def __str__(self):
        return self.name
