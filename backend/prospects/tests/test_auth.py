from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='S3curePass!')

    def test_api_requires_authentication(self):
        response = self.client.get('/api/leads/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_success_returns_token(self):
        response = self.client.post('/api/auth/login/', {'username': 'alice', 'password': 'S3curePass!'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')
        self.assertTrue(Token.objects.filter(user=self.user, key=response.data['token']).exists())

    def test_login_wrong_password_rejected(self):
        response = self.client.post('/api/auth/login/', {'username': 'alice', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_user_rejected(self):
        response = self.client.post('/api/auth/login/', {'username': 'ghost', 'password': 'whatever'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_endpoint_requires_valid_token(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'alice')

    def test_logout_revokes_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

        # Le même token ne doit plus donner accès
        response = self.client.get('/api/leads/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unsubscribe_view_is_public(self):
        """La désinscription doit rester accessible sans authentification."""
        import uuid
        response = self.client.get(f'/api/unsubscribe/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
