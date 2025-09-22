import json
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.reverse import reverse
from rest_framework.decorators import api_view
import rest_framework.status as status

from photo_gis.models import Photo, Tag
from photo_gis.serializers import PhotoSerializer, TagSerializer

# Create your views here.

@api_view(['GET'])
def api_root(request: Request):
    return Response({
            "photos": {
                "description": "List of photos owned by the authenticated user.",
                "items": reverse("photo-list", request=request)
            },
            "tags": {
                "description": "List of all the tags that can be associated with a photo.",
                "items" : reverse("tag-list", request=request)
            }
    })


class PhotoList(GenericAPIView):
    def get(self, request: Request):
        photos = Photo.objects.all()
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data)
    
    def post(self, request: Request):
        """
        Uploads one or more photos and associated tags.
        Request body must have the key 'images' where the value is a list of image files
        Request body may have the key 'tags' where the value is a list of lists of strings
            the ith inner list corresponds to the list of tags associated with the ith image
        """
        images = request.FILES.getlist('images', [])
        if not images:
            return Response({"message": "No images submitted."}, status=status.HTTP_400_BAD_REQUEST)
        
        tags_lists = request.data.getlist('tags', [])

        data = [{"image" : image, "tags": json.loads(tags)} for image, tags in zip(images, tags_lists)]
        serializer = PhotoSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message" : "Photos created"}, status=status.HTTP_200_OK)


class TagList(GenericAPIView):
    def get(self, request: Request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)