from unittest.mock import patch

from rest_framework import status

from prospects.models import DiscoveredProspect, Lead
from .base import AuthenticatedAPITestCase
from .factories import make_campaign


def make_prospect(**kwargs):
    defaults = {
        "google_place_id": f"place-{DiscoveredProspect.objects.count()}",
        "name": "Boulangerie Test",
        "address": "1 rue Test, Paris",
        "phone": "0123456789",
        "category": "boulangerie",
        "search_location": "Paris",
    }
    defaults.update(kwargs)
    return DiscoveredProspect.objects.create(**defaults)


class DiscoveredProspectSearchTests(AuthenticatedAPITestCase):
    @patch("prospects.views.search_businesses_without_website")
    def test_search_requires_query(self, mock_search):
        response = self.client.post("/api/discovered-prospects/search/", {"location": "Paris"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_search.assert_not_called()

    @patch("prospects.views.search_businesses_without_website")
    def test_search_returns_result(self, mock_search):
        mock_search.return_value = {"found": 5, "without_website": 2, "created": 2, "duplicates": 0}
        response = self.client.post(
            "/api/discovered-prospects/search/", {"query": "boulangerie", "location": "Paris"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["created"], 2)
        mock_search.assert_called_once_with("boulangerie", "Paris")

    @patch("prospects.views.search_businesses_without_website", side_effect=ValueError("clé manquante"))
    def test_search_missing_config_returns_400(self, mock_search):
        response = self.client.post("/api/discovered-prospects/search/", {"query": "boulangerie"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("prospects.views.search_businesses_without_website")
    def test_search_api_error_returns_502(self, mock_search):
        import requests
        mock_search.side_effect = requests.HTTPError("403")
        response = self.client.post("/api/discovered-prospects/search/", {"query": "boulangerie"})
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)


class DiscoveredProspectConvertTests(AuthenticatedAPITestCase):
    def test_convert_without_email_rejected(self):
        prospect = make_prospect(email="")
        response = self.client.post(f"/api/discovered-prospects/{prospect.id}/convert/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_convert_creates_lead(self):
        prospect = make_prospect(email="contact@boulangerie-test.fr", name="Boulangerie Dupont")
        response = self.client.post(f"/api/discovered-prospects/{prospect.id}/convert/")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lead.objects.filter(email="contact@boulangerie-test.fr").exists())

        prospect.refresh_from_db()
        self.assertEqual(prospect.status, "CONVERTED")
        self.assertIsNotNone(prospect.converted_lead)
        self.assertEqual(prospect.converted_lead.company, "Boulangerie Dupont")

    def test_convert_assigns_campaign(self):
        campaign = make_campaign()
        prospect = make_prospect(email="contact@boulangerie-test.fr")
        response = self.client.post(
            f"/api/discovered-prospects/{prospect.id}/convert/", {"campaign": str(campaign.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lead = Lead.objects.get(email="contact@boulangerie-test.fr")
        self.assertEqual(lead.campaign_id, campaign.id)

    def test_convert_twice_rejected(self):
        prospect = make_prospect(email="contact@boulangerie-test.fr")
        self.client.post(f"/api/discovered-prospects/{prospect.id}/convert/")
        response = self.client.post(f"/api/discovered-prospects/{prospect.id}/convert/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_convert_duplicate_email_rejected(self):
        from .factories import make_lead
        make_lead(email="existing@example.com")
        prospect = make_prospect(email="existing@example.com")
        response = self.client.post(f"/api/discovered-prospects/{prospect.id}/convert/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DiscoveredProspectCrudTests(AuthenticatedAPITestCase):
    def test_list_filters_by_status(self):
        make_prospect(google_place_id="p1", status="NEW")
        make_prospect(google_place_id="p2", status="DISCARDED")

        response = self.client.get("/api/discovered-prospects/", {"status": "NEW"})
        names = [item["google_place_id"] for item in response.data["results"]]
        self.assertEqual(names, ["p1"])

    def test_update_email(self):
        prospect = make_prospect()
        response = self.client.patch(
            f"/api/discovered-prospects/{prospect.id}/", {"email": "new@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prospect.refresh_from_db()
        self.assertEqual(prospect.email, "new@example.com")

    def test_discard(self):
        prospect = make_prospect()
        response = self.client.patch(
            f"/api/discovered-prospects/{prospect.id}/", {"status": "DISCARDED"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prospect.refresh_from_db()
        self.assertEqual(prospect.status, "DISCARDED")
