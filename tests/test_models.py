import unittest
from sqlalchemy import create_engine
import transaction
import os

from taskq.models import (
    DBSession,
    Base,
    Task,
)
import taskq.models as models

DB_NAME = 'test_taskq.db'
DB_URL = 'sqlite:///%s' % DB_NAME


def func4test(*args, **kw):
    return 'func4test %s %s' % (args, kw)


def func4testdoc(*args, **kw):
    """Display the function name

    This line should be ignored
    """
    return 'func4testdoc %s %s' % (args, kw)


def func4testfailed(*args, **kw):
    raise Exception('Failing function')


class Class4Test(object):

    def run(self):
        return 'Class4Test.run is called'


class TestTask(unittest.TestCase):

    def setUp(self):
        engine = create_engine(DB_URL)
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        transaction.abort()
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def test___init__(self):
        task = Task()
        self.assertEqual(task._args, None)
        self.assertEqual(task._func_name, None)
        self.assertEqual(task._kw, None)
        self.assertEqual(task._instance, None)

        # init_on_load is called when we load from DB
        Task.create(func4test)
        task = Task.query.one()
        self.assertEqual(task._args, [])
        self.assertEqual(task._func_name, 'tests.test_models.func4test')
        self.assertEqual(task._kw, {})
        self.assertEqual(task._instance, None)

    def test_dump_func(self):
        task = Task()
        dic = task.dump_func()
        expected = {
            '_args': None,
            '_func_name': None,
            '_kw': None,
            '_instance': None
        }
        self.assertEqual(dic, expected)

    def test_load_func(self):
        task = Task()
        dic = task.dump_func()
        expected = {
            '_args': None,
            '_func_name': None,
            '_kw': None,
            '_instance': None
        }
        self.assertEqual(dic, expected)
        task.func = {
            '_args': '_args',
            '_func_name': '_func_name''',
            '_kw': '_kw',
            '_instance': '_instance'
        }
        task.load_func()
        self.assertEqual(task._args, '_args')
        self.assertEqual(task._kw, '_kw')
        self.assertEqual(task._func_name, '_func_name')
        self.assertEqual(task._instance, '_instance')

    def test_create(self):
        expected = {
            '_args': None,
            '_func_name': 'tests.test_models.func4test',
            '_kw': None,
            '_instance': None
        }
        task = Task.create(func4test)
        self.assertEqual(task._args, expected['_args'])
        self.assertEqual(task._func_name, expected['_func_name'])
        self.assertEqual(task._kw, expected['_kw'])
        self.assertEqual(task._instance, expected['_instance'])
        DBSession.add(task)
        self.assertEqual(task.func, expected)
        self.assertEqual(task.description, 'func4test')
        self.assertTrue(task.creation_date)

        # With parameters
        expected = {
            '_args': [1, 2],
            '_func_name': 'tests.test_models.func4test',
            '_kw': {'a': 1, 'b': 2},
            '_instance': None
        }
        task = Task.create(func4test, [1, 2], {'a': 1, 'b': 2}, 'Hello world')
        self.assertEqual(task._args, expected['_args'])
        self.assertEqual(task._func_name, expected['_func_name'])
        self.assertEqual(task._kw, expected['_kw'])
        self.assertEqual(task._instance, expected['_instance'])
        DBSession.add(task)
        self.assertEqual(task.func, expected)
        self.assertEqual(task.description, 'Hello world')

        # Test with docstring
        expected = {
            '_args': None,
            '_func_name': 'tests.test_models.func4testdoc',
            '_kw': None,
            '_instance': None
        }
        task = Task.create(func4testdoc)
        self.assertEqual(task._args, expected['_args'])
        self.assertEqual(task._func_name, expected['_func_name'])
        self.assertEqual(task._kw, expected['_kw'])
        self.assertEqual(task._instance, expected['_instance'])
        DBSession.add(task)
        self.assertEqual(task.func, expected)
        self.assertEqual(task.description, 'Display the function name')

        # Test with object
        expected = {
            '_args': None,
            '_func_name': 'run',
            '_kw': None,
        }
        o = Class4Test()
        task = Task.create(o.run)
        self.assertEqual(task._args, expected['_args'])
        self.assertEqual(task._func_name, expected['_func_name'])
        self.assertEqual(task._kw, expected['_kw'])
        self.assertTrue(task._instance)
        DBSession.add(task)
        for k, v in expected.iteritems():
            self.assertEqual(task.func[k], v)
        self.assertTrue(task.func['_instance'])
        self.assertEqual(task.description, 'run')

    def test_perform(self):
        task = Task.create(func4test)
        DBSession.add(task)
        res = task.perform()
        expected = 'func4test () {}'
        self.assertEqual(res, expected)
        self.assertEqual(task.result, expected)
        self.assertEqual(task.status, models.TASK_STATUS_FINISHED)
        self.assertTrue(task.start_date)
        self.assertTrue(task.end_date)

        task = Task.create(func4test, [1, 2], {'a': 1, 'b': 2}, 'Hello world')
        DBSession.add(task)
        res = task.perform()
        expected = "func4test (1, 2) {'a': 1, 'b': 2}"
        self.assertEqual(res, expected)
        self.assertEqual(task.result, expected)
        self.assertEqual(task.status, models.TASK_STATUS_FINISHED)

        o = Class4Test()
        task = Task.create(o.run)
        DBSession.add(task)
        res = task.perform()
        expected = "Class4Test.run is called"
        self.assertEqual(res, expected)
        self.assertEqual(task.result, expected)
        self.assertEqual(task.status, models.TASK_STATUS_FINISHED)

        task = Task.create(func4testfailed)
        DBSession.add(task)
        res = task.perform()
        self.assertIn('Failing function', res)
        self.assertEqual(task.status, models.TASK_STATUS_FAILED)
