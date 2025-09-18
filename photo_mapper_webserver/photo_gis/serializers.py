from rest_framework.serializers import ModelSerializer, ReadOnlyField, PrimaryKeyRelatedField
from photo_gis.models import Photo, Tag

class PhotoSerializer(ModelSerializer):
    owner = ReadOnlyField(source="owner.username")
    
    class Meta:
        model = Photo
        fields = ["owner", "image", "location", "datetime", "tags"]


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "photos"]