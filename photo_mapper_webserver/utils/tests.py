from unittest import TestCase
from unittest.mock import MagicMock

from datetime import datetime
from PIL import ExifTags
from PIL.TiffImagePlugin import IFDRational
from django.contrib.gis.geos import Point

from .exif_reader import get_datetime, get_location, DMS_to_decimal
from .exif_exception import DateTimeMissingException, GPSInfoMissingException

class ExifReaderTests(TestCase):

    def setUp(self):
        super().setUp()

    def test_get_datetime(self):
        dt = datetime(2025, 1, 1, 1, 1, 1)
        exif_mock = MagicMock()

        exif_ifd_mock = {
            ExifTags.Base.DateTimeOriginal: dt.strftime(R"%Y:%m:%d %H:%M:%S")
        }

        exif_mock.get_ifd.return_value = exif_ifd_mock    

        result = get_datetime(exif_mock)

        self.assertEqual(result, dt)

    def test_get_datetime_raises_exception_if_datetime_missing(self):
        exif_mock = MagicMock()

        exif_ifd_mock = {
            ExifTags.Base.DateTimeOriginal: None
         }

        exif_mock.get_ifd.return_value = exif_ifd_mock    

        with self.assertRaises(DateTimeMissingException):
            get_datetime(exif_mock)

    def test_get_datetime_raises_exception_if_exif_ifd_missing(self):
        exif_mock = MagicMock()
        exif_mock.get_ifd.return_value = { }

        with self.assertRaises(DateTimeMissingException):
            get_datetime(exif_mock)

    def test_DMS_to_decimal(self):
        degrees = IFDRational(1,1)
        minutes = IFDRational(51)
        seconds = IFDRational(169, 5)
        direction = "N"
        expected_value = float(degrees + minutes/60 + seconds/3600)
        self.assertAlmostEqual(expected_value, DMS_to_decimal(degrees, minutes, seconds, direction))

        degrees = IFDRational(57)
        minutes = IFDRational(37)
        seconds = IFDRational(247, 10)
        direction = "E"
        expected_value = float(degrees + minutes/60 + seconds/3600)
        self.assertAlmostEqual(expected_value, DMS_to_decimal(degrees, minutes, seconds, direction))

        # Test direction 'W' or 'S' correctly reverses the direction
        degrees = IFDRational(157)
        minutes = IFDRational(23)
        seconds = IFDRational(95, 2)
        direction = "W"
        expected_value = -float(degrees + minutes/60 + seconds/3600)
        self.assertAlmostEqual(expected_value, DMS_to_decimal(degrees, minutes, seconds, direction))

        degrees = IFDRational(20)
        minutes = IFDRational(26)
        seconds = IFDRational(181, 5)
        direction = "S"
        expected_value = -float(degrees + minutes/60 + seconds/3600)
        self.assertAlmostEqual(expected_value, DMS_to_decimal(degrees, minutes, seconds, direction))

    def test_get_location(self):
        exif_mock = MagicMock()

        gps_ifd_mock = {
            ExifTags.GPS.GPSLatitudeRef: "N",
            ExifTags.GPS.GPSLatitude: (
                IFDRational(1,1),
                IFDRational(51),
                IFDRational(169, 5)
            ),
            ExifTags.GPS.GPSLongitudeRef: "W",
            ExifTags.GPS.GPSLongitude: (
                IFDRational(157),
                IFDRational(23),
                IFDRational(95, 2)
            )
        }

        exif_mock.get_ifd.return_value = gps_ifd_mock

        expected_value = Point(-157.39652777777778, 1.859388888888889)

        self.assertAlmostEqual(get_location(exif_mock), expected_value)

    def test_get_location_raises_exception_if_Location_Missing(self):
        exif_mock = MagicMock()

        gps_ifd_mock = {
            ExifTags.GPS.GPSLatitudeRef: "N",
            ExifTags.GPS.GPSLatitude: (
                IFDRational(1,1),
                IFDRational(51),
                IFDRational(169, 5)
            ),
            ExifTags.GPS.GPSLongitude: (
                IFDRational(157),
                IFDRational(23),
                IFDRational(95, 2)
            )
        }

        exif_mock.get_ifd.return_value = gps_ifd_mock

        with self.assertRaises(GPSInfoMissingException):
            get_location(exif_mock)


        gps_ifd_mock = {
            ExifTags.GPS.GPSLatitudeRef: "N",
            ExifTags.GPS.GPSLatitude: (
                IFDRational(1,1),
                IFDRational(51),
                IFDRational(169, 5)
            ),
            ExifTags.GPS.GPSLongitudeRef: "W",
        }

        with self.assertRaises(GPSInfoMissingException):
            get_location(exif_mock)

    def test_get_location_raises_exception_if_gps_ifd_missing(self):
        exif_mock = MagicMock()

        exif_mock.get_ifd.return_value = { }

        with self.assertRaises(GPSInfoMissingException):
            get_location(exif_mock)