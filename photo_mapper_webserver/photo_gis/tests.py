import shutil
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.db.utils import IntegrityError

from .models import Tag, Photo, photo_directory_path

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
        self.timestamp = datetime.now(tz=timezone.utc)

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

    def test_tags_unique(self):
        duplicate_tag = {
            "name" : self.tags[0].name
        }

        with self.assertRaises(IntegrityError):
            Tag.objects.create(**duplicate_tag)

    def tearDown(self):
        super().tearDown()

        shutil.rmtree('images')