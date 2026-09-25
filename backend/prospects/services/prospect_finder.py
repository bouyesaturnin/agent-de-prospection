import requests
from django.conf import settings

from prospects.models import AgentLog, DiscoveredProspect

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.websiteUri",
])


def search_businesses_without_website(query: str, location: str) -> dict:
    """
    Interroge l'API Google Places (Text Search) pour '{query} {location}' et
    enregistre en base les établissements qui n'ont PAS de site web renseigné
    (les meilleurs prospects pour une offre de création de site).

    Ne fait jamais d'envoi ni de contact : construit juste une liste à qualifier
    (DiscoveredProspect, status='NEW') dans laquelle l'email doit être complété
    à la main avant de pouvoir convertir en vrai Lead.

    Lève ValueError si la clé API est absente.
    """
    if not settings.GOOGLE_PLACES_API_KEY:
        raise ValueError("La variable GOOGLE_PLACES_API_KEY est manquante dans la configuration.")

    text_query = f"{query} à {location}" if location else query

    response = requests.post(
        PLACES_SEARCH_URL,
        json={"textQuery": text_query, "languageCode": "fr"},
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": FIELD_MASK,
        },
        timeout=15,
    )
    response.raise_for_status()
    places = response.json().get("places", [])

    found = len(places)
    without_website = 0
    created = 0
    duplicates = 0

    for place in places:
        if place.get("websiteUri"):
            continue  # a déjà un site : pas un prospect pour cette offre
        without_website += 1

        place_id = place.get("id")
        if not place_id:
            continue

        _, was_created = DiscoveredProspect.objects.get_or_create(
            google_place_id=place_id,
            defaults={
                "name": place.get("displayName", {}).get("text", "") or "(nom inconnu)",
                "address": place.get("formattedAddress", ""),
                "phone": place.get("nationalPhoneNumber", ""),
                "category": query,
                "search_location": location,
            },
        )
        if was_created:
            created += 1
        else:
            duplicates += 1

    AgentLog.objects.create(
        action='PROSPECTS_DISCOVERED',
        level='INFO',
        message=(
            f"Recherche '{text_query}' : {found} établissement(s) trouvé(s), "
            f"{without_website} sans site web, {created} nouveau(x), {duplicates} déjà connu(s)."
        ),
    )

    return {
        "found": found,
        "without_website": without_website,
        "created": created,
        "duplicates": duplicates,
    }
