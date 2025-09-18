from django.urls import path
from photo_gis.views import api_root, PhotoList, TagList

urlpatterns = [
    path("", api_root ),
    path("photos/", PhotoList.as_view(), name="photo-list"),
    path("tags/", TagList.as_view(), name="tag-list"),
]