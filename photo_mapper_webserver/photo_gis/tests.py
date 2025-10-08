import shutil
import uuid
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db.utils import IntegrityError, DataError
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from PIL import Image, ExifTags

from .models import Tag, Photo, photo_directory_path
from .views import PhotoList

# Create your tests here.

User = get_user_model()


class PhotoTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create(username="fakeuser", password="fakepwd")
        tag_names = ["urban", "nature"]
        self.tags = Tag.objects.bulk_create(
            [Tag(name=name) for name in tag_names]
        )
        
        self.image_files = [
            SimpleUploadedFile(
                name="DSCF0001.jpg",
                content=b"imagedata",
                content_type="image/jpeg"
            ),
            SimpleUploadedFile(
                name="DSCF0002.jpg",
                content=b"imagedata",
                content_type="image/jpeg"
            )
        ]

        self.location = Point(0.0, 0.0, srid=4326) # lon/lat
        self.timestamp = datetime(2205, 1, 1, 12, 0, 0).replace(tzinfo=timezone.utc)

        self.photos = Photo.objects.bulk_create(
            [Photo(
                owner = self.owner,
                image = image_file,
                location = self.location,
                timestamp = self.timestamp + timedelta(minutes=i),
            ) for i, image_file in enumerate(self.image_files)]
        )        

    def test_photo_directory_path(self):
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.owner = self.owner
        filename = "DSCF0001.jpg"

        expected_path = f"images/{self.owner.id}/{mock_instance.id.hex}.jpg"
        actual_path = photo_directory_path(mock_instance, filename)

        self.assertEqual(actual_path, expected_path)

    def test_photo_model(self):
        self.assertIsInstance(self.photos[0], Photo)

        self.assertEqual(self.photos[0].owner, self.owner)
        self.assertEqual(self.photos[0].location, self.location)
        self.assertEqual(self.photos[0].timestamp, self.timestamp)
        self.assertIsInstance(self.photos[0].id, uuid.UUID)

        # Test photo upload directory
        expected_path = f"images/{self.owner.id}/{self.photos[0].id.hex}.jpg"
        actual_path = self.photos[0].image.path
        self.assertIn(expected_path, actual_path.replace("\\", "/")) # Windows style path to Unix style path


    def test_photo_tag_relationship(self):
        self.photos[0].tags.add(*Tag.objects.all())
        self.photos[1].tags.add(Tag.objects.get(name="urban"))

        # Relationship from photo to tag
        self.assertEqual(self.photos[0].tags.count(), 2)
        self.assertEqual(self.photos[1].tags.count(), 1)
        self.assertEqual(self.photos[0].tags.first().name, "urban")

        # Relationship from tag to photo
        self.assertEqual(self.photos[0].tags.count(), 2)
        self.assertEqual(self.photos[1].tags.count(), 1)
        
        related_photos = [photo.id for photo in self.tags[0].photos.all()]
        for photo in self.photos:
            self.assertIn(photo.id, related_photos)

    def test_photo_unique_time_and_place(self):
        duplicate_photo = {
                "owner": self.owner,
                "image": self.image_files[0],
                "location": self.location,
                "timestamp": self.timestamp
        }

        with self.assertRaises(IntegrityError):
            Photo.objects.create(**duplicate_photo)

    
    def test_photo_view_get_only_returns_photos_belonging_to_authenticated_user(self):
        second_user = User.objects.create(username="Second User", password="123456789")
        photo = Photo.objects.create(
                owner = second_user,
                image = SimpleUploadedFile(
                    name="DSCF0004.jpg",
                    content=b"imagedata",
                    content_type="image/jpeg"
                ),
                location = self.location,
                timestamp = self.timestamp + timedelta(minutes=30)
        )
        
        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.get('/collections/photos/')
        force_authenticate(request, second_user)
        response = view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].get("owner"), "Second User")
    
    def test_photo_view_get_does_not_allow_unauthenticated_users(self):
        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.get('/collections/photos/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_photo_post(self):
        image = Image.new('RGB', (100, 100))
        exif = self._write_exif_data(image.getexif(), timestamp=self.timestamp, point=Point(1,1))
        tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmpfile, exif=exif)
        tmpfile.seek(0)

        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.post(
            '/collections/photos/', 
            {
                "image": tmpfile
            },
            format='multipart'
        )

        force_authenticate(request, self.owner)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Photo.objects.all().count(), 3)
        tmpfile.close()
    
    def test_photo_post_returns_error_for_identical_time_and_place(self):
        image = Image.new('RGB', (100, 100))
        exif = self._write_exif_data(image.getexif(), timestamp=self.timestamp, point=Point(0, 0))
        tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmpfile, exif=exif)
        tmpfile.seek(0)

        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.post(
            '/collections/photos/', 
            {
                "image": tmpfile
            },
            format='multipart'
        )

        force_authenticate(request, self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tmpfile.close()

    def test_photo_post_returns_error_if_photo_missing_gps_info(self):
        image = Image.new('RGB', (100, 100))
        exif = self._write_timestamp(image.getexif(), timestamp=self.timestamp+timedelta(1))
        tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmpfile, exif=exif)
        tmpfile.seek(0)

        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.post(
            '/collections/photos/', 
            {
                "image": tmpfile
            },
            format='multipart'
        )

        force_authenticate(request, self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tmpfile.close()

    def test_photo_post_returns_error_if_photo_missing_timestamp(self):
        image = Image.new('RGB', (100, 100))
        exif = self._write_gps_info(image.getexif(), point=Point(0, 0))
        tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmpfile, exif=exif)
        tmpfile.seek(0)

        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.post(
            '/collections/photos/', 
            {
                "image": tmpfile
            },
            format='multipart'
        )

        force_authenticate(request, self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tmpfile.close()

    def _write_exif_data(self, exif, timestamp:datetime, point:Point):
        exif = self._write_timestamp(exif, timestamp)
        exif = self._write_gps_info(exif, point)
        return exif

    def _write_gps_info(self, exif, point):
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_ifd[ExifTags.GPS.GPSLatitude] = (point.y, 0, 0)
        gps_ifd[ExifTags.GPS.GPSLatitudeRef] = 'N'
        gps_ifd[ExifTags.GPS.GPSLongitude] = (point.x, 0, 0)
        gps_ifd[ExifTags.GPS.GPSLongitudeRef] = 'E'

        return exif

    def _write_timestamp(self, exif, timestamp):
        exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
        exif_ifd[ExifTags.Base.DateTimeOriginal] = timestamp.strftime(r"%Y:%m:%d %H:%M:%S")
        exif_ifd[ExifTags.Base.OffsetTimeOriginal] = "+00:00"
        return exif

    def tearDown(self):
        super().tearDown()

        shutil.rmtree('images')

class TagTests(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="urban")

    def test_tag_model(self):
        self.assertEqual(self.tag.name, "urban")

    def test_tags_unique_case_insensitive(self):
        duplicate_tag = {
            "name" : "uRbAn"
        }

        with self.assertRaises(IntegrityError):
            Tag.objects.create(**duplicate_tag)

    def test_tags_length_constraints(self):
        long_tag = {
            "name" : "urbanphotostakenatgoldenhourinaprilormarchonpartiallycloudydays"
        }

        with self.assertRaises(DataError):
            Tag.objects.create(**long_tag)
    
    def test_tag_view_does_not_allow_unauthenticated_users(self):
        factory = APIRequestFactory()
        view = PhotoList.as_view()
        request = factory.get('/collections/tags/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)