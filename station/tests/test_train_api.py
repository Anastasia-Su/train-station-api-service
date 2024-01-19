import tempfile
import os

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from station.models import Train, TrainType, Journey, Route, Station
from station.serializers import (
    TrainListSerializer,
    TrainDetailSerializer,
    JourneySerializer,
    JourneyListSerializer,
)

TRAIN_URL = reverse("station:train-list")
JOURNEY_URL = reverse("station:journey-list")


def payload(key=None, value=None):
    pld = {
        "name": "Sample train",
        "cargo_num": 5,
        "places_in_cargo": 100,
    }
    if key and value:
        pld[key] = value
    return pld


def sample_train(**params):
    defaults = {
        "name": "Sample train",
        "cargo_num": 5,
        "places_in_cargo": 100,
    }
    defaults.update(params)

    return Train.objects.create(**defaults)


def sample_journey(i, **params):
    station1 = Station.objects.create(name=f"ST{i}", latitude=1.1, longitude=6.8)
    station2 = Station.objects.create(name=f"ST{i + 1}", latitude=9.1, longitude=56.8)
    route = Route.objects.create(source=station1, destination=station2)

    defaults = {
        "departure_time": "2024-01-11 14:00:00",
        "arrival_time": "2024-01-12 06:00:00",
        "train": sample_train(),
        "route": route,
    }
    defaults.update(params)

    return Journey.objects.create(**defaults)


def image_upload_url(train_id):
    """Return URL for recipe image upload"""
    return reverse("station:train-upload-image", args=[train_id])


def detail_url(train_id):
    return reverse("station:train-detail", args=[train_id])


class UnauthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TRAIN_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "test@test.com",
            "testpass",
        )
        self.client.force_authenticate(self.user)

    def test_list_trains(self):
        sample_train()
        sample_train()

        res = self.client.get(TRAIN_URL)

        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_trains_by_type(self):
        type1 = TrainType.objects.create(name="type1")
        type2 = TrainType.objects.create(name="type2")
        another_type = TrainType.objects.create(name="another")

        train1 = sample_train(train_type=type1)
        train2 = sample_train(train_type=type2)
        train3 = sample_train(train_type=another_type)

        res = self.client.get(TRAIN_URL, {"type": "type"})

        serializer1 = TrainListSerializer(train1)
        serializer2 = TrainListSerializer(train2)
        serializer3 = TrainListSerializer(train3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_journeys_by_date(self):
        journey1 = sample_journey(1, departure_time="2024-01-11")
        journey2 = sample_journey(3, departure_time="2023-12-12")

        res = self.client.get(JOURNEY_URL, {"date": "2024-01-11"})

        serializer1 = JourneyListSerializer(journey1)
        serializer2 = JourneyListSerializer(journey2)

        for item in res.data:
            self.assertIn(serializer1.data["departure_time"], item["departure_time"])
            self.assertNotIn(serializer2.data["departure_time"], item["departure_time"])

    def test_filter_journeys_by_train_id(self):
        journey1 = sample_journey(1)
        journey2 = sample_journey(3)

        res = self.client.get(JOURNEY_URL, {"train": 1})

        serializer1 = JourneySerializer(journey1)
        serializer2 = JourneySerializer(journey2)

        for item in res.data:
            self.assertEqual(serializer1.data["train"], item["id"])
            self.assertNotEqual(serializer2.data["train"], item["id"])

    def test_retrieve_train_detail(self):
        train = sample_train()

        url = detail_url(train.id)
        res = self.client.get(url)

        serializer = TrainDetailSerializer(train)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_train_forbidden(self):
        res = self.client.post(TRAIN_URL, payload())

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminTrainApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "admin@admin.com", "testpass", is_staff=True
        )
        self.client.force_authenticate(self.user)

    def test_create_train(self):
        payload_var = payload()
        res = self.client.post(TRAIN_URL, payload_var)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        train = Train.objects.get(id=res.data["id"])
        for key in payload_var:
            self.assertEqual(payload_var[key], getattr(train, key))

    def test_create_train_with_type(self):
        ttype = TrainType.objects.create(name="Type1")
        payload_var = payload("train_type", ttype.pk)

        res = self.client.post(TRAIN_URL, payload_var)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        train_type = Train.objects.get(id=res.data["id"]).train_type
        self.assertEqual(ttype, train_type)

#
# class TrainImageUploadTests(TestCase):
#     def setUp(self):
#         self.client = APIClient()
#         self.user = get_user_model().objects.create_superuser(
#             "admin@myproject.com", "password", is_staff=True
#         )
#         self.client.force_authenticate(self.user)
#         self.train = sample_train()
#         self.journey = sample_journey(1, train=self.train)
#
#     def tearDown(self):
#         self.train.image.delete()
#
#     def test_upload_image_to_train(self):
#         """Test uploading an image to train"""
#         url = image_upload_url(self.train.id)
#         with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
#             img = Image.new("RGB", (10, 10))
#             img.save(ntf, format="JPEG")
#             ntf.seek(0)
#             res = self.client.post(url, {"image": ntf}, format="multipart")
#         self.train.refresh_from_db()
#
#         self.assertEqual(res.status_code, status.HTTP_200_OK)
#         self.assertIn("image", res.data)
#         self.assertTrue(os.path.exists(self.train.image.path))
#
#     def test_upload_image_bad_request(self):
#         """Test uploading an invalid image"""
#         url = image_upload_url(self.train.id)
#         res = self.client.post(url, {"image": "not image"}, format="multipart")
#
#         self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
#
#     def test_post_image_to_train_list_should_not_work(self):
#         url = TRAIN_URL
#         with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
#             img = Image.new("RGB", (10, 10))
#             img.save(ntf, format="JPEG")
#             ntf.seek(0)
#             res = self.client.post(
#                 url,
#                 {
#                     "name": "Sample train with img",
#                     "cargo_num": 5,
#                     "places_in_cargo": 100,
#                     "image": ntf,
#                 },
#                 format="multipart",
#             )
#
#         self.assertEqual(res.status_code, status.HTTP_201_CREATED)
#         train = Train.objects.get(name="Sample train with img")
#         self.assertFalse(train.image)
#
#     def test_image_url_is_shown_on_train_detail(self):
#         url = image_upload_url(self.train.id)
#         with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
#             img = Image.new("RGB", (10, 10))
#             img.save(ntf, format="JPEG")
#             ntf.seek(0)
#             self.client.post(url, {"image": ntf}, format="multipart")
#         res = self.client.get(detail_url(self.train.id))
#
#         self.assertIn("image", res.data)
#
#     def test_image_url_is_shown_on_train_list(self):
#         url = image_upload_url(self.train.id)
#         with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
#             img = Image.new("RGB", (10, 10))
#             img.save(ntf, format="JPEG")
#             ntf.seek(0)
#             self.client.post(url, {"image": ntf}, format="multipart")
#         res = self.client.get(TRAIN_URL)
#
#         self.assertIn("image", res.data[0].keys())
#
#     def test_image_url_is_shown_on_train_detail(self):
#         url = image_upload_url(self.train.id)
#         with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
#             img = Image.new("RGB", (10, 10))
#             img.save(ntf, format="JPEG")
#             ntf.seek(0)
#             self.client.post(url, {"image": ntf}, format="multipart")
#         res = self.client.get(JOURNEY_URL)
#
#         self.assertIn("train_image", res.data[0].keys())
