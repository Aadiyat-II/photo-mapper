from rest_framework.serializers import HyperlinkedIdentityField, ModelSerializer, HyperlinkedModelSerializer, ReadOnlyField, ListField, CharField,  StringRelatedField
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from utils.exif_reader import read_photo_metadata
from utils.resize_photo import resize_image

from photo_gis.models import Photo, Tag

class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name"]


class PhotoSerializer(GeoFeatureModelSerializer):
    owner = ReadOnlyField(source="owner.username")
    tags = ListField(
        child = CharField(max_length=50), 
        write_only=True,
    )
    # TODO: max_length is a property of Tag. Putting it here again as a magic number is bad practice

    tag_names = StringRelatedField(many=True, source="tags", read_only=True)

    url = HyperlinkedIdentityField(
        view_name="photo-detail",
        lookup_field="id"
    )

    class Meta:
        model = Photo
        fields = ["url", "owner", "image", "location", "timestamp", "tags", "tag_names"]
        read_only_fields = ["owner", "location", "timestamp"]
        geo_field = "location"

    def create(self, validated_data):
        owner = self.context.get("owner")

        image_file = validated_data.pop("image")
        timestamp, loc = read_photo_metadata(image_file)
        resized_image = resize_image(image_file)

        validated_data["timestamp"] = timestamp
        validated_data["location"] = loc
        validated_data["owner"] = owner
        validated_data["image"] = resized_image

        tags = [Tag.objects.get_or_create(name=tag)[0] for tag in validated_data.pop("tags")]

        photo = Photo.objects.create(**validated_data)
        photo.tags.set(tags)

        return photo
    
    def update(self, instance, validated_data):
        tag_data = validated_data.pop("tags", None)

        instance = super().update(instance, validated_data)

        if tag_data is not None:
            tags = [Tag.objects.get_or_create(name=name)[0] for name in tag_data]
            instance.tags.set(tags)

        return instance
    
    def validate_tags(self, value):
        return list({tag.lower().strip() for tag in value if tag.strip()})