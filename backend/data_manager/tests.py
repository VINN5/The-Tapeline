from django.test import TestCase
from django.core.files.base import ContentFile
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from accounts.models import User
from connectors.models import DatabaseConnection
from data_manager.models import ExtractionJob, ExtractedRecord, StoredFile


def make_user(username='testuser', role='user'):
    return User.objects.create_user(username=username, password='Pass1234!', role=role)


def make_connection(owner):
    conn = DatabaseConnection(
        owner=owner,
        name='Test Connection',
        db_type='postgresql',
        host='localhost',
        port=5432,
        database_name='testdb',
        username='dbuser',
    )
    conn.password = 'dbpass'
    conn.save()
    return conn


def make_job(owner, connection, status='completed'):
    job = ExtractionJob.objects.create(
        owner=owner,
        connection=connection,
        table_name='users',
        batch_size=100,
        status=status,
    )
    return job


def make_record(job, data=None):
    return ExtractedRecord.objects.create(
        job=job,
        data=data or {'id': 1, 'name': 'Alice'},
    )


def make_stored_file(owner, job, file_format='json'):
    sf = StoredFile.objects.create(
        owner=owner,
        job=job,
        file_format=file_format,
        source_metadata={'table_name': 'users', 'record_count': 1},
    )
    sf.file.save(f'test_{sf.id}.{file_format}', ContentFile(b'{}'))
    return sf


class ExtractionJobModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.conn = make_connection(self.user)

    def test_job_str(self):
        job = make_job(self.user, self.conn)
        self.assertIn('users', str(job))
        self.assertIn('completed', str(job))

    def test_job_default_status_is_pending(self):
        job = ExtractionJob.objects.create(
            owner=self.user,
            connection=self.conn,
            table_name='orders',
            batch_size=50,
        )
        self.assertEqual(job.status, 'pending')

    def test_records_count_via_serializer(self):
        job = make_job(self.user, self.conn)
        make_record(job)
        make_record(job, {'id': 2, 'name': 'Bob'})
        self.assertEqual(job.records.count(), 2)


class ExtractedRecordModelTest(TestCase):

    def setUp(self):
        self.user = make_user('recuser')
        self.conn = make_connection(self.user)
        self.job = make_job(self.user, self.conn)

    def test_record_str(self):
        record = make_record(self.job)
        self.assertIn(str(self.job.id), str(record))

    def test_record_is_edited_defaults_false(self):
        record = make_record(self.job)
        self.assertFalse(record.is_edited)

    def test_record_stores_json_data(self):
        data = {'id': 99, 'email': 'test@example.com', 'active': True}
        record = make_record(self.job, data)
        self.assertEqual(record.data['email'], 'test@example.com')


class StoredFileModelTest(TestCase):

    def setUp(self):
        self.user = make_user('fileuser')
        self.conn = make_connection(self.user)
        self.job = make_job(self.user, self.conn)

    def test_stored_file_str(self):
        sf = make_stored_file(self.user, self.job)
        self.assertIn('fileuser', str(sf))

    def test_shared_with_is_empty_by_default(self):
        sf = make_stored_file(self.user, self.job)
        self.assertEqual(sf.shared_with.count(), 0)

    def test_share_with_user(self):
        sf = make_stored_file(self.user, self.job)
        other = make_user('sharedwith')
        sf.shared_with.add(other)
        self.assertIn(other, sf.shared_with.all())


class ExtractionJobViewSetTest(APITestCase):

    def setUp(self):
        self.user = make_user('jobowner')
        self.other = make_user('jobother')
        self.admin = make_user('jobadmin', role='admin')
        self.conn = make_connection(self.user)
        self.client.force_authenticate(user=self.user)

    @patch('data_manager.views.get_connector')
    def test_create_job_success(self, mock_get_connector):
        mock_connector = MagicMock()
        mock_connector.fetch_data.return_value = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
        ]
        mock_get_connector.return_value = mock_connector
        response = self.client.post('/api/jobs/', {
            'connection': self.conn.id,
            'table_name': 'users',
            'batch_size': 100,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(response.data['records_count'], 2)

    @patch('data_manager.views.get_connector')
    def test_create_job_connector_failure(self, mock_get_connector):
        mock_get_connector.side_effect = Exception('Connection refused')
        response = self.client.post('/api/jobs/', {
            'connection': self.conn.id,
            'table_name': 'users',
            'batch_size': 100,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        job = ExtractionJob.objects.get(connection=self.conn)
        self.assertEqual(job.status, 'failed')

    def test_list_jobs_only_shows_own(self):
        other_conn = make_connection(self.other)
        make_job(self.user, self.conn)
        make_job(self.other, other_conn)
        response = self.client.get('/api/jobs/')
        jobs = response.data.get('results', response.data)
        owners = [j['owner'] for j in jobs]
        self.assertTrue(all('jobowner' in o for o in owners))

    def test_admin_sees_all_jobs(self):
        other_conn = make_connection(self.other)
        make_job(self.user, self.conn)
        make_job(self.other, other_conn)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/jobs/')
        jobs = response.data.get('results', response.data)
        self.assertGreaterEqual(len(jobs), 2)

    def test_records_endpoint(self):
        job = make_job(self.user, self.conn)
        make_record(job, {'id': 1, 'val': 'a'})
        make_record(job, {'id': 2, 'val': 'b'})
        response = self.client.get(f'/api/jobs/{job.id}/records/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_cannot_access_other_users_job_records(self):
        other_conn = make_connection(self.other)
        job = make_job(self.other, other_conn)
        response = self.client.get(f'/api/jobs/{job.id}/records/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_updates_records_and_creates_file(self):
        job = make_job(self.user, self.conn)
        record = make_record(job, {'id': 1, 'name': 'Original'})
        response = self.client.post(f'/api/jobs/{job.id}/submit/', {
            'records': [{'id': record.id, 'data': {'id': 1, 'name': 'Updated'}}],
            'format': 'json',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('file', response.data)
        record.refresh_from_db()
        self.assertTrue(record.is_edited)
        self.assertEqual(record.data['name'], 'Updated')

    def test_submit_with_csv_format(self):
        job = make_job(self.user, self.conn)
        record = make_record(job, {'id': 1, 'name': 'Alice'})
        response = self.client.post(f'/api/jobs/{job.id}/submit/', {
            'records': [{'id': record.id, 'data': {'id': 1, 'name': 'Alice'}}],
            'format': 'csv',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['file']['file_format'], 'csv')

    def test_submit_with_no_records_returns_error(self):
        job = make_job(self.user, self.conn)
        response = self.client.post(f'/api/jobs/{job.id}/submit/', {
            'records': [],
            'format': 'json',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_access_jobs(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StoredFileViewSetTest(APITestCase):

    def setUp(self):
        self.user = make_user('fileowner')
        self.other = make_user('fileother')
        self.admin = make_user('fileadmin', role='admin')
        self.conn = make_connection(self.user)
        self.job = make_job(self.user, self.conn)
        self.client.force_authenticate(user=self.user)

    def test_list_files_only_shows_own_and_shared(self):
        own_file = make_stored_file(self.user, self.job)
        other_conn = make_connection(self.other)
        other_job = make_job(self.other, other_conn)
        other_file = make_stored_file(self.other, other_job)
        shared_file = make_stored_file(self.other, other_job)
        shared_file.shared_with.add(self.user)
        response = self.client.get('/api/files/')
        files = response.data.get('results', response.data)
        ids = [f['id'] for f in files]
        self.assertIn(own_file.id, ids)
        self.assertIn(shared_file.id, ids)
        self.assertNotIn(other_file.id, ids)

    def test_admin_sees_all_files(self):
        make_stored_file(self.user, self.job)
        other_conn = make_connection(self.other)
        other_job = make_job(self.other, other_conn)
        make_stored_file(self.other, other_job)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/files/')
        files = response.data.get('results', response.data)
        self.assertGreaterEqual(len(files), 2)

    def test_share_file_with_valid_user(self):
        sf = make_stored_file(self.user, self.job)
        response = self.client.post(f'/api/files/{sf.id}/share/', {'username': 'fileother'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sf.refresh_from_db()
        self.assertIn(self.other, sf.shared_with.all())

    def test_share_file_with_nonexistent_user(self):
        sf = make_stored_file(self.user, self.job)
        response = self.client.post(f'/api/files/{sf.id}/share/', {'username': 'ghost'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_share_file(self):
        other_conn = make_connection(self.other)
        other_job = make_job(self.other, other_conn)
        sf = make_stored_file(self.other, other_job)
        sf.shared_with.add(self.user)
        response = self.client.post(f'/api/files/{sf.id}/share/', {'username': 'fileadmin'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_file(self):
        sf = make_stored_file(self.user, self.job)
        response = self.client.delete(f'/api/files/{sf.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_other_users_file(self):
        other_conn = make_connection(self.other)
        other_job = make_job(self.other, other_conn)
        sf = make_stored_file(self.other, other_job)
        response = self.client.delete(f'/api/files/{sf.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_access_files(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/files/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)