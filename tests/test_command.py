import unittest
from mock import patch, Mock
import os
from sqlalchemy import create_engine
import ConfigParser
from taskq import command
from taskq.models import (
    DBSession,
    Base,
    Task,
)
import taskq.models as models
import transaction
import multiprocessing


DB_NAME = 'test_taskq.db'
DB_URL = 'sqlite:///%s' % DB_NAME


def func2lock(*args, **kw):
    engine = create_engine(DB_URL)
    models.engine = engine
    DBSession.configure(bind=engine)
    idtask = command.lock_task(models)
    return idtask


def func4test(*args, **kw):
    return 'test'


class TestCommand(unittest.TestCase):

    def setUp(self):
        engine = create_engine(DB_URL)
        models.engine = engine
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

    def tearDown(self):
        transaction.abort()
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)

    def test__lock_task(self):
        Task.create(func2lock)
        connection = models.engine.connect()
        idtask = command._lock_task(connection, models)
        self.assertEqual(idtask, 1)
        task = models.Task.query.get(1)
        self.assertEqual(task.status, models.TASK_STATUS_IN_PROGRESS)
        self.assertTrue(task.pid)
        idtask = command._lock_task(connection, models)
        self.assertEqual(idtask, None)

    def test_lock_task(self):
        for i in range(4):
            Task.create(func2lock)
        pool = multiprocessing.Pool(processes=4)
        res = pool.map(func2lock, [{}, {}, {}, {}])
        res.sort()
        self.assertEqual(res, [1, 2, 3, 4])
        rows = models.Task.query.filter_by(pid=None).all()
        self.assertEqual(len(rows), 0)

    def test__run(self):
        res = command._run(models)
        self.assertEqual(res, False)
        Task.create(func4test)
        res = command._run(models)
        self.assertEqual(res, True)
        task = Task.query.get(1)
        self.assertEqual(task.status, models.TASK_STATUS_FINISHED)
        self.assertTrue(task.pid)
        self.assertEqual(task.result, 'test')

    def test_parse_config_file(self):
        config = ConfigParser.RawConfigParser()
        with patch('ConfigParser.ConfigParser', return_value=config):
            res = command.parse_config_file('/fake')
            self.assertEqual(res, None)

            # Make sure loggers are loaded
            with patch('logging.config.fileConfig', return_value=None) as m:
                config.add_section('loggers')
                config.set('loggers', 'key', 'value')
                res = command.parse_config_file('/fake')
                self.assertEqual(res, None)
                m.assert_called_with('/fake')

            # No option in taskq section, we get the default
            config.add_section('taskq')
            res = command.parse_config_file('/fake')
            expected = {
                'sigterm': True,
                'timeout': 60,
            }
            self.assertEqual(res, expected)

            config.set('taskq', 'sigterm', 'false')
            config.set('taskq', 'timeout', '5')
            config.set('taskq', 'sqla_url', '//my_url')
            res = command.parse_config_file('/fake')
            expected = {
                'sigterm': False,
                'timeout': 5,
                'sqla_url': '//my_url',
            }
            self.assertEqual(res, expected)

    def test_parse_options(self):
        res = command.parse_options([])
        expected = {
            'sigterm': True,
            'sqla_url': None,
            'config_filename': None,
        }
        self.assertEqual(res, expected)

        res = command.parse_options([], parse_timeout=True)
        expected = {
            'sigterm': True,
            'sqla_url': None,
            'config_filename': None,
            'timeout': 60,
        }
        self.assertEqual(res, expected)

        options = ['-s', '-t', '90', '-u', 'sqlite://fake.db']
        res = command.parse_options(options, parse_timeout=True)
        expected = {
            'sigterm': False,
            'sqla_url': 'sqlite://fake.db',
            'config_filename': None,
            'timeout': 90,
        }
        self.assertEqual(res, expected)

        options = ['-s', '-t', '90',
                   '-u', 'sqlite://fake.db',
                   '-c', 'fake.ini']
        res = command.parse_options(options, parse_timeout=True)
        expected = {
            'sigterm': False,
            'sqla_url': 'sqlite://fake.db',
            'config_filename': 'fake.ini',
            'timeout': 90,
        }
        self.assertEqual(res, expected)

        config = ConfigParser.RawConfigParser()
        with patch('ConfigParser.ConfigParser', return_value=config):
            config.add_section('taskq')
            config.set('taskq', 'timeout', '5')
            res = command.parse_config_file('/fake')

            expected = {
                'sigterm': True,
                'timeout': 5,
            }
            self.assertEqual(res, expected)
