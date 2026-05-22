from django.contrib.auth.models import User
from .base import BaseAPITestCase


class AuthAPITestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPassword123',
        )

    def test_login_with_username(self):
        response = self.client.post(
            '/api/v1/auth/login',
            {'identifier': 'testuser', 'password': 'TestPassword123'},
            format='json',
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['username'], 'testuser')

    def test_login_with_email(self):
        response = self.client.post(
            '/api/v1/auth/login',
            {'identifier': 'testuser@example.com', 'password': 'TestPassword123'},
            format='json',
        )
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['email'], 'testuser@example.com')

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            '/api/v1/auth/login',
            {'identifier': 'testuser', 'password': 'wrongpassword'},
            format='json',
        )
        data = response.json()
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
        self.assertIn('Invalid credentials', data['message'])
