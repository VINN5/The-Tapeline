from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from accounts.models import User
from connectors.models import DatabaseConnection


def make_connection(owner, name='Test DB', db_type='postgresql'):
    conn = DatabaseConnection(
        owner=owner,
        name=name,
        db_type=db_type,
        host='localhost',
        port=5432,
        database_name='testdb',
        username='testuser',
    )
    conn.password = 'plaintextpassword'
    conn.save()
    return conn


class DatabaseConnectionModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='Pass1234!')

    def test_password_is_encrypted_at_rest(self):
        conn = make_connection(self.user)
        self.assertNotEqual(conn._password, 'plaintextpassword')

    def test_password_decrypts_correctly(self):
        conn = make_connection(self.user)
        self.assertEqual(conn.password, 'plaintextpassword')

    def test_str_representation(self):
        conn = make_connection(self.user)
        self.assertIn('Test DB', str(conn))
        self.assertIn('postgresql', str(conn))
        self.assertIn('owner', str(conn))

    def test_unique_together_owner_and_name(self):
        make_connection(self.user, name='UniqueDB')
        with self.assertRaises(Exception):
            make_connection(self.user, name='UniqueDB')

    def test_different_owners_can_have_same_name(self):
        other_user = User.objects.create_user(username='other', password='Pass1234!')
        make_connection(self.user, name='SharedName')
        conn2 = make_connection(other_user, name='SharedName')
        self.assertIsNotNone(conn2.pk)


class DatabaseConnectionViewSetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='connuser', password='Pass1234!')
        self.other_user = User.objects.create_user(username='otheruser', password='Pass1234!')
        self.admin = User.objects.create_user(username='adminuser', password='Pass1234!', role='admin')
        self.client.force_authenticate(user=self.user)

    def _connection_payload(self, name='My DB'):
        return {
            'name': name,
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database_name': 'mydb',
            'username': 'dbuser',
            'password': 'dbpass',
        }

    def test_create_connection(self):
        response = self.client.post('/api/connections/', self._connection_payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'My DB')
        self.assertNotIn('password', response.data)

    def test_list_connections_only_shows_own(self):
        make_connection(self.user, name='Mine')
        make_connection(self.other_user, name='Theirs')
        response = self.client.get('/api/connections/')
        names = [c['name'] for c in response.data.get('results', response.data)]
        self.assertIn('Mine', names)
        self.assertNotIn('Theirs', names)

    def test_admin_sees_all_connections(self):
        make_connection(self.user, name='UserConn')
        make_connection(self.other_user, name='OtherConn')
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/connections/')
        names = [c['name'] for c in response.data.get('results', response.data)]
        self.assertIn('UserConn', names)
        self.assertIn('OtherConn', names)

    def test_cannot_access_other_users_connection(self):
        conn = make_connection(self.other_user, name='Private')
        response = self.client.get(f'/api/connections/{conn.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_list_connections(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/connections/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_own_connection(self):
        conn = make_connection(self.user, name='ToDelete')
        response = self.client.delete(f'/api/connections/{conn.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch('connectors.views.get_connector')
    def test_test_connection_success(self, mock_get_connector):
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = True
        mock_get_connector.return_value = mock_connector
        conn = make_connection(self.user, name='TestConn')
        response = self.client.post(f'/api/connections/{conn.id}/test/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('connectors.views.get_connector')
    def test_tables_endpoint(self, mock_get_connector):
        mock_connector = MagicMock()
        mock_connector.get_tables.return_value = ['users', 'orders']
        mock_get_connector.return_value = mock_connector
        conn = make_connection(self.user, name='TablesConn')
        response = self.client.get(f'/api/connections/{conn.id}/tables/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tables', response.data)