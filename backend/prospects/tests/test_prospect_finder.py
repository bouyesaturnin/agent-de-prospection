from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings

from prospects.models import AgentLog, DiscoveredProspect
from prospects.services.prospect_finder import search_businesses_without_website


def fake_places_response(places):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"places": places}
    resp.raise_for_status.return_value = None
    return resp


def place(place_id, name, has_website=False, phone="0123456789", address="1 rue Test, Paris"):
    data = {
        "id": place_id,
        "displayName": {"text": name},
        "formattedAddress": address,
        "nationalPhoneNumber": phone,
    }
    if has_website:
        data["websiteUri"] = "https://example.com"
    return data


@override_settings(GOOGLE_PLACES_API_KEY="test-key")
class SearchBusinessesTests(TestCase):
    @patch("prospects.services.prospect_finder.requests.post")
    def test_filters_out_places_with_website(self, mock_post):
        mock_post.return_value = fake_places_response([
            place("place-1", "Boulangerie Sans Site", has_website=False),
            place("place-2", "Restaurant Avec Site", has_website=True),
        ])

        result = search_businesses_without_website("boulangerie", "Paris")

        self.assertEqual(result, {"found": 2, "without_website": 1, "created": 1, "duplicates": 0})
        self.assertEqual(DiscoveredProspect.objects.count(), 1)
        self.assertEqual(DiscoveredProspect.objects.get().name, "Boulangerie Sans Site")

    @patch("prospects.services.prospect_finder.requests.post")
    def test_second_search_deduplicates_by_place_id(self, mock_post):
        mock_post.return_value = fake_places_response([place("place-1", "Boulangerie Sans Site")])

        search_businesses_without_website("boulangerie", "Paris")
        result = search_businesses_without_website("boulangerie", "Paris")

        self.assertEqual(result["created"], 0)
        self.assertEqual(result["duplicates"], 1)
        self.assertEqual(DiscoveredProspect.objects.count(), 1)

    @patch("prospects.services.prospect_finder.requests.post")
    def test_creates_agent_log(self, mock_post):
        mock_post.return_value = fake_places_response([place("place-1", "Boulangerie Sans Site")])
        search_businesses_without_website("boulangerie", "Paris")
        self.assertTrue(AgentLog.objects.filter(action="PROSPECTS_DISCOVERED").exists())

    @patch("prospects.services.prospect_finder.requests.post")
    def test_uses_correct_request_headers_and_field_mask(self, mock_post):
        mock_post.return_value = fake_places_response([])
        search_businesses_without_website("plombier", "Créteil")

        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["X-Goog-Api-Key"], "test-key")
        self.assertIn("places.websiteUri", kwargs["headers"]["X-Goog-FieldMask"])
        self.assertEqual(kwargs["json"]["textQuery"], "plombier à Créteil")

    @patch("prospects.services.prospect_finder.requests.post")
    def test_propagates_http_error(self, mock_post):
        resp = MagicMock()
        resp.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        mock_post.return_value = resp

        with self.assertRaises(requests.HTTPError):
            search_businesses_without_website("plombier", "Paris")


@override_settings(GOOGLE_PLACES_API_KEY="")
class SearchBusinessesConfigTests(TestCase):
    @patch("prospects.services.prospect_finder.requests.post")
    def test_missing_api_key_raises_without_calling_api(self, mock_post):
        with self.assertRaises(ValueError):
            search_businesses_without_website("plombier", "Paris")
        mock_post.assert_not_called()
