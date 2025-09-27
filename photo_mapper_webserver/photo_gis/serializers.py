from rest_framework.serializers import ModelSerializer, ReadOnlyField, ListField, CharField,  StringRelatedField
from photo_gis.models import Photo, Tag
from utils.exif_reader import read_photo_metadata


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]


class PhotoSerializer(ModelSerializer):
    owner = ReadOnlyField(source="owner.username")
    tags = ListField(
        child = CharField(max_length=50), 
        write_only=True,
    )
    # TODO: max_length is a property of Tag. Putting it here again as a magic number is bad practice

    tag_names = StringRelatedField(many=True, source="tags", read_only=True)

    class Meta:
        model = Photo
        fields = ["owner", "image", "location", "timestamp", "tags", "tag_names"]
        read_only_fields = ["owner", "location", "timestamp"]

    def create(self, validated_data):
        from django.contrib.auth import get_user_model
        # TODO: Dummy user for now. Replace with authenticated user when auth implemented
        User = get_user_model()
        owner = User.objects.get(pk=1) 

        image = validated_data.get("image")
        timestamp, loc = read_photo_metadata(image)
        validated_data["timestamp"] = timestamp
        validated_data["location"] = loc
        validated_data["owner"] = owner

        tags = [Tag.objects.get_or_create(name=tag)[0] for tag in validated_data.pop("tags")]

        photo = Photo.objects.create(**validated_data)
        photo.tags.set(tags)

        return photo