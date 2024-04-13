import json
import os
import pathlib
import shutil
import unittest

import fastapi


class Test(unittest.IsolatedAsyncioTestCase):
    tmp_folder = pathlib.Path('./tmp').absolute()
    os.environ['DATABASE_FILENAME'] = str(tmp_folder / 'data.db')
    os.environ['UPLOAD_FOLDER'] = str(tmp_folder / 'uploads')
    os.environ['FAMILIARS_FOLDER'] = str(tmp_folder / 'familiars')

    models: 'models' = None
    main: 'main' = None
    scope = {
        'type': 'http',
        'server': ('127.0.0.1', 8000),
        'scheme': 'http',
        'method': 'GET',
        'path': '/upload/1',
        'headers': [(b'host', b'localhost:8000'), ],
    }
    base_request = fastapi.Request(scope=scope)

    def setUp(self):
        self.models = None
        self.main = None
        shutil.rmtree(self.tmp_folder, ignore_errors=True)
        if not os.path.exists(self.tmp_folder):
            os.mkdir(self.tmp_folder)
        import models
        import main
        self.models = models
        self.main = main
        self.models.create_models()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.models = None
        cls.main = None
        shutil.rmtree(cls.tmp_folder, ignore_errors=True)

    def tearDown(self):
        self.models.database.close()
        self.models = None
        self.main = None
        shutil.rmtree(self.tmp_folder, ignore_errors=True)

    async def test_virtual_db(self):
        with self.models.database:
            uploads = self.models.Upload.select()
        self.assertEqual(0, len(uploads))
        uploads = None

    async def test_get_upload(self):
        with self.models.database:
            self.models.Upload.create(id=10, filepath='cool_test.jpg')
        request = fastapi.Request(scope=self.scope)
        result = await self.main.get_upload(request, 10)
        self.assertEqual(200, result.status_code)
        body = json.loads(result.body)
        result = None
        self.assertIn('upload_id', body['data'])

    async def test_get_upload_file(self):
        file = pathlib.Path(__file__).absolute()
        with self.models.database:
            self.models.Upload.create(id=10, filepath=str(file))
        result: fastapi.responses.FileResponse = await self.main.get_upload_file(self.base_request, 10)
        self.assertEqual(fastapi.responses.FileResponse, type(result))
        self.assertEqual(200, result.status_code)

    async def test_get_upload_file2(self):
        file = pathlib.Path(__file__)
        file = file.with_stem(file.stem+'_not_exists')
        with self.models.database:
            self.models.Upload.create(id=10, filepath=str(file))
        result: fastapi.responses.FileResponse = await self.main.get_upload_file(self.base_request, 10)
        self.assertIsInstance(result, fastapi.responses.Response)
        self.assertEqual(404, result.status_code)
