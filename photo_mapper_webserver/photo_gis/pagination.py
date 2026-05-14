from rest_framework_gis.pagination import GeoJsonPagination

class PhotoGeoJsonPagination(GeoJsonPagination):
    # Standard DRF attributes still apply
    page_size = 10
    page_size_query_param = 'page_size' # Allow frontend to request ?page_size=50
    max_page_size = 100