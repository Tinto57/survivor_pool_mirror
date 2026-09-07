from unittest.mock import patch

from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    def test_health_ok_is_public_and_returns_version(self):
        response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")
        self.assertEqual(response.data["version"], settings.APP_VERSION)
        self.assertEqual(response.data["checks"], {"database": "ok", "cache": "ok"})

    def test_health_reports_503_when_database_is_down(self):
        with patch("config.views.connections") as mock_connections:
            mock_connections.__getitem__.side_effect = Exception("boom")
            response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["checks"]["database"], "error")

    def test_health_reports_503_when_cache_is_down(self):
        with patch("config.views.cache") as mock_cache:
            mock_cache.set.side_effect = Exception("boom")
            response = self.client.get("/api/v1/health/")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "error")
        self.assertEqual(response.data["checks"]["cache"], "error")
