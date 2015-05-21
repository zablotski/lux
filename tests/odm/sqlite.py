import json

from pulsar.apps.test import test_timeout

from lux.utils import test


class TestSql(test.AppTestCase):
    config_file = 'tests.odm'
    config_params = {'DATASTORE': 'sqlite://'}

    def test_odm(self):
        odm = self.app.odm()
        tables = odm.tables()
        self.assertTrue(tables)

    def test_rest_model(self):
        from tests.odm import CRUDTask
        model = CRUDTask.model
        self.assertEqual(model.name, 'task')
        columns = model.columns(self.app)
        self.assertTrue(columns)

    def test_simple_session(self):
        app = self.app
        odm = app.odm()
        with odm.begin() as session:
            self.assertEqual(session.app, app)
            user = odm.user(first_name='Luca')
            session.add(user)

        self.assertTrue(user.id)
        self.assertEqual(user.first_name, 'Luca')
        self.assertFalse(user.is_superuser())

    def test_get_tasks(self):
        request = self.client.get('/tasks')
        response = request.response
        self.assertEqual(response.status_code, 200)
        data = self.json(response)
        self.assertIsInstance(data, list)

    def test_metadata(self):
        request = self.client.get('/tasks/metadata')
        response = request.response
        self.assertEqual(response.status_code, 200)
        data = self.json(response)
        self.assertIsInstance(data, dict)
        self.assertIsInstance(data['columns'], list)

    def test_create_task(self):
        self._create_task()

    def test_update_task(self):
        task = self._create_task('This is another task')
        # Update task
        request = self.client.post('/tasks/%d' % task['id'],
                                   body={'done': True},
                                   content_type='application/json')
        response = request.response
        self.assertEqual(response.status_code, 200)
        data = self.json(response)
        self.assertEqual(data['id'], task['id'])
        self.assertEqual(data['done'], True)
        #
        request = self.client.get('/tasks/%d' % task['id'])
        response = request.response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], task['id'])
        self.assertEqual(data['done'], True)

    def test_delete_task(self):
        task = self._create_task('A task to be deleted')
        # Delete task
        request = self.client.delete('/tasks/%d' % task['id'])
        response = request.response
        self.assertEqual(response.status_code, 204)
        #
        request = self.client.get('/tasks/%d' % task['id'])
        response = request.response
        self.assertEqual(response.status_code, 404)

    def _create_task(self, txt='This is a task'):
        data = {'subject': txt}
        request = self.client.post('/tasks', body=data,
                                   content_type='application/json')
        response = request.response
        self.assertEqual(response.status_code, 201)
        data = self.json(response)
        self.assertIsInstance(data, dict)
        self.assertTrue('id' in data)
        self.assertEqual(data['subject'], txt)
        self.assertTrue('created' in data)
        self.assertFalse(data['done'])
        return data
