import shutil
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.gis.geos import Point

from .models import Tag, Photo, photo_directory_path

# Create your tests here.

User = get_user_model()


class PhotoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="fakeuser", password="fakepwd")
        tag_names = ["urban", "nature"]
        self.tags = Tag.objects.bulk_create(
            [Tag(name=name) for name in tag_names]
        )
        
        image_files = [
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
        self.datetime = datetime.now(tz=timezone.utc)

        self.photos = Photo.objects.bulk_create(
            [Photo(
                user = self.user,
                image = image_file,
                location = self.location,
                datetime = self.datetime,
            ) for image_file in image_files]
        )        

    def test_photo_directory_path(self):
        mock_instance = MagicMock()
        mock_instance.id = uuid.uuid4()
        mock_instance.user = self.user
        filename = "DSCF0001.jpg"

        expected_path = f"images/{self.user.id}/{mock_instance.id.hex}.jpg"
        actual_path = photo_directory_path(mock_instance, filename)

        self.assertEqual(actual_path, expected_path)

    def test_photo_model(self):
        self.assertIsInstance(self.photos[0], Photo)

        self.assertEqual(self.photos[0].user, self.user)
        self.assertEqual(self.photos[0].location, self.location)
        self.assertEqual(self.photos[0].datetime, self.datetime)
        self.assertIsInstance(self.photos[0].id, uuid.UUID)

        # Test photo upload directory
        expected_path = f"images/{self.user.id}/{self.photos[0].id.hex}.jpg"
        actual_path = self.photos[0].image.path
        self.assertIn(expected_path, actual_path.replace("\\", "/")) # Windows style path to Unix style path

    def test_tag_model(self):
        self.assertEqual(self.tags[0].name, "urban")

    def test_photo_tag_relationship(self):
        self.photos[0].tags.add(*Tag.objects.all())
        self.photos[1].tags.add(Tag.objects.get(name="urban"))

        # Relationship from photo to tag
        self.assertEqual(self.photos[0].tags.count(), 2)
        self.assertEqual(self.photos[1].tags.count(), 1)
        self.assertEqual(self.photos[0].tags.first().name, "urban")

        # Relationship from tag to photo
        self.assertEqual(self.tags[0].tags.count(), 2)
        self.assertEqual(self.tags[1].tags.count(), 1)
        
        related_photos = [photo.id for photo in self.tags[0].tags.all()]
        for photo in self.photos:
            self.assertIn(photo.id, related_photos)

    def tearDown(self):
        super().tearDown()

        shutil.rmtree('images')