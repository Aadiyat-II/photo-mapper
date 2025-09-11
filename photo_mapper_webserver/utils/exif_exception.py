class ExifException(Exception):
    """Base class for all exceptions raised by this module"""

class DateTimeMissingException(ExifException):
    """The photo is missing DateTime information in its exif metadata"""

class GPSInfoMissingException(ExifException):
    """The photo is missing GPS information in its exif metadata"""