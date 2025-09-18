import os
import uuid
from pathlib import Path
from django.contrib.gis.db import models
from django.conf import settings

# Create your models here.

def photo_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_filename = f"{instance.id.hex}.{ext}"
    return os.path.join("images", str(instance.owner.id), unique_filename).replace('\\', '/')


class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    

class Photo(models.Model):    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=photo_directory_path)
    location = models.PointField()
    datetime = models.DateTimeField()
    tags = models.ManyToManyField(Tag, related_name='tags')

    def __str__(self):
        return f"{self.location.wkt}:{self.datetime}"