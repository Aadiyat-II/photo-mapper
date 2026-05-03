from django.urls import path
from photo_gis.views import api_root, PhotoList, PhotoDetail, TagList

urlpatterns = [
    path("", api_root ),
    path("photos/", PhotoList.as_view(), name="photo-list"),
    path("photos/<str:id>/", PhotoDetail.as_view(), name="photo-detail"),
    path("tags/", TagList.as_view(), name="tag-list"),
]