from django.db import models

class Stop(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()

class TravelRoute(models.Model):
    start_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='start_routes')
    end_stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name='end_routes')
    distance = models.FloatField()
    duration = models.IntegerField()
class TransitStop(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
