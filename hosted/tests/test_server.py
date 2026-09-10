import importlib
import os
import tempfile
import unittest

from fastapi.testclient import TestClient


class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        os.environ['STUDIO_DATA'] = cls.temp.name
        os.environ['STUDIO_PASSWORD'] = 'test-secret-not-a-production-password'
        cls.server = importlib.import_module('hosted.server')
        cls.client = TestClient(cls.server.app)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def login(self):
        self.client.cookies.clear()
        self.assertEqual(self.client.post('/api/login', json={'password': os.environ['STUDIO_PASSWORD']}).status_code, 200)

    def test_private_media_and_job_list(self):
        self.client.cookies.clear()
        self.assertEqual(self.client.get('/api/jobs').status_code, 401)
        self.assertEqual(self.client.get('/api/jobs/'+'a'*32+'/file/source').status_code, 401)
        self.assertEqual(self.client.get('/health').status_code, 200)

    def test_upload_order_and_invalid_media_rejection(self):
        self.login()
        job = self.client.post('/api/jobs', json={'title': 'Test'}).json()['id']
        route = '/api/jobs/'+job
        self.assertEqual(self.client.put(route+'/upload/video?offset=0', content=b'not video').status_code, 200)
        self.assertEqual(self.client.put(route+'/upload/video?offset=0', content=b'overwrite').status_code, 409)
        self.assertEqual(self.client.put(route+'/upload/other?offset=0', content=b'x').status_code, 400)
        self.assertEqual(self.client.post(route+'/start').status_code, 400)
        self.assertEqual(self.client.delete(route).status_code, 200)

    def test_cross_origin_write_is_denied(self):
        self.login()
        self.assertEqual(self.client.post('/api/jobs', json={}, headers={'origin':'https://unrelated.example'}).status_code, 403)

    def test_media_path_is_restricted(self):
        self.login()
        self.assertEqual(self.client.get('/api/jobs/not-an-id').status_code, 404)


if __name__ == '__main__': unittest.main()
