from datetime import datetime
from PIL import Image, ExifTags
from PIL.TiffImagePlugin import IFDRational
from django.core.files.uploadedfile import UploadedFile
from django.contrib.gis.geos import Point

from .exif_exception import DateTimeMissingException, GPSInfoMissingException


def read_photo_metadata(photo_file: UploadedFile):
    """
    Read EXIF datetime and location data from a Django Uploaded File object using Pillow

    Args:
        photo_file: The file uploaded

    Returns:
        dt: Datetime object representing when when the photo was taken. Timezone naive.
        point: Geos Point object representing where the photo was taken.
    """

    with Image.open(photo_file) as img:
        exif = img.getexif()
    
    dt = get_datetime(exif)
    point = get_location(exif)

    return dt, point
        
def get_datetime(exif: Image.Exif):
    """
    Extracts datetime information from an Exif object.

    Args:
        exif: An Image.Exif object containing photo metadata
    Returns
        Datetime object representing when the photo was taken. Timezone naive.
    """
    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif) # Returns an empty dict if ExifTags.IFD.Exif not found
    try:
        dt = datetime.strptime(
            exif_ifd.get(ExifTags.Base.DateTimeOriginal), 
            r"%Y:%m:%d %H:%M:%S"
        )
    except TypeError:
        raise DateTimeMissingException("Exif data missing datetime.")
    else:
        return dt 

def get_location(exif: Image.Exif):
    """
    Extracts GPS location from an Exif object

    Args:
        exif: An Image.Exif object containing photo metadata
    Returns:
        A Geos Point object representing where the photo was taken. 
    """
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    
    try:
        lat = DMS_to_decimal(
            *gps_ifd.get(ExifTags.GPS.GPSLatitude),
            gps_ifd.get(ExifTags.GPS.GPSLatitudeRef)
        )
        
        lon = DMS_to_decimal(
            *gps_ifd.get(ExifTags.GPS.GPSLongitude),
            gps_ifd.get(ExifTags.GPS.GPSLongitudeRef)
        )
    except TypeError:
        raise GPSInfoMissingException("Exif data missing GSP Info.")
    except AttributeError:
        raise GPSInfoMissingException("Exif data missing GPS Info")
    else:
        return Point(lon, lat)

def DMS_to_decimal(degrees: IFDRational, minutes: IFDRational, seconds: IFDRational, direction: str):
    """
    Converts GPS coordinates from DMS format to decimal degree format.

    Args:
        degrees: Degree component of DMS format
        minutes: Minutes component of DMS format
        seconds: Seconds component of DMS format
        direction: Cardinal direction 'N', 'S', 'E' or 'W'
    Returns:
        Coordinates in decimal degree format
    """
    decimal = float(degrees + minutes/60 + seconds/3600)
    
    if direction.upper() in ("S", "W"):
        decimal = -decimal
    
    return decimal