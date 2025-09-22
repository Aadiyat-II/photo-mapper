from rest_framework.serializers import ModelSerializer, ReadOnlyField
from photo_gis.models import Photo, Tag
from utils.exif_reader import read_photo_metadata


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]


class PhotoSerializer(ModelSerializer):
    owner = ReadOnlyField(source="owner.username")
    tags = TagSerializer(many=True)

    class Meta:
        model = Photo
        fields = ["owner", "image", "location", "datetime", "tags"]
        read_only_fields = ["owner", "location", "datetime",]

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        # TODO: Dummy user for now. Replace with authenticated user when auth implemented
        User = get_user_model()
        owner = User.objects.get(pk=1) 

        image = validated_data.get("image")
        dt, loc = read_photo_metadata(image)
        validated_data["datetime"] = dt
        validated_data["location"] = loc
        validated_data["owner"] = owner

        tag_data = validated_data.pop("tags")
        tags = [Tag.objects.get_or_create(name=tag["name"])[0] for tag in tag_data]

        photo = Photo.objects.create(**validated_data)
        photo.tags.set(tags)

        return photo