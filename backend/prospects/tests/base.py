from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthenticatedAPITestCase(APITestCase):
    """Base commune pour les tests d'API : crée un utilisateur et authentifie le client."""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username='tester', password='S3curePass!')
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
