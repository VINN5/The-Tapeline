from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import User


class UserModelTest(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='Admin1234!', role='admin'
        )
        self.user = User.objects.create_user(
            username='user', password='User1234!', role='user'
        )

    def test_is_admin_returns_true_for_admin(self):
        self.assertTrue(self.admin.is_admin())

    def test_is_admin_returns_false_for_user(self):
        self.assertFalse(self.user.is_admin())

    def test_default_role_is_user(self):
        u = User.objects.create_user(username='newuser', password='New1234!')
        self.assertEqual(u.role, 'user')

    def test_str_representation(self):
        self.assertEqual(str(self.admin), 'admin (admin)')
        self.assertEqual(str(self.user), 'user (user)')


class RegisterViewTest(APITestCase):

    def test_register_success(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'user',
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_register_passwords_do_not_match(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123!',
            'password2': 'DifferentPass123!',
            'role': 'user',
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username='existing', password='Pass1234!')
        data = {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post('/api/accounts/register/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser', password='Pass1234!', email='p@example.com'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')
        self.assertEqual(response.data['email'], 'p@example.com')

    def test_update_profile_email(self):
        response = self.client.patch('/api/accounts/profile/', {'email': 'new@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'new@example.com')

    def test_profile_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='logoutuser', password='Pass1234!'
        )
        self.client.force_authenticate(user=self.user)

    def test_logout_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/accounts/logout/', {'refresh': 'token'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_token(self):
        response = self.client.post('/api/accounts/logout/', {'refresh': 'invalidtoken'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserListViewTest(APITestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='Admin1234!', role='admin'
        )
        self.user = User.objects.create_user(
            username='regularuser', password='Pass1234!', role='user'
        )

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data.get('results', response.data)
        self.assertGreaterEqual(len(users), 2)

    def test_regular_user_gets_empty_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users = response.data.get('results', response.data)
        self.assertEqual(len(users), 0)

    def test_unauthenticated_cannot_list_users(self):
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)