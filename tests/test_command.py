import unittest
from mock import patch, Mock
import os
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import ConfigParser
from sqla_taskq import command
from sqla_taskq.models import (
    DBSession,
    Base,
    Task,
)
import sqla_taskq.models as models
import transaction
import multiprocessing


DB_NAME = 'test_sqla_taskq.db'
DB_URL = 'sqlite:///%s' % DB_NAME


def func2lock(*args, **kw):
    engine = create_engine(DB_URL)
    models.engine = engine
    DBSession.configure(bind=engine)
    idtask = command.lock_task(models)
    return idtask


def func4test(*args, **kw):
    return 'test'


class TestSignal(unittest.TestCase):

    def test_sigterm_handler(self):
        self.assertEqual(command.loop, True)
        command.sigterm_handler(666, None)
        self.assertEqual(command.loop, False)
        command.loop = True

    def test_sigterm_kill_handler(self):
        self.assertEqual(command.loop, True)
        try:
            command.sigterm_kill_handler(666, None)
            assert(False)  # pragma: no cover
        except SystemExit, e:
            self.assertEqual(str(e), '0')
            self.assertEqual(command.loop, False)
        finally:
            command.loop = True


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
        self.assertTrue(task.lock_date)
        idtask = command._lock_task(connection, models)
        self.assertEqual(idtask, None)

        Task.create(func2lock, unique_key='mykey')
        idtask = command._lock_task(connection, models)
        self.assertEqual(idtask, 2)

        Task.create(func2lock, unique_key='mykey')
        # Will not lock this new task since it's the same unique key than the
        # previous one which is not finished
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

        class Err(OperationalError):
            def __init__(self):
                pass

        def f(*args, **kw):
            raise Err()

        with patch('sqla_taskq.command._lock_task', side_effect=f):
            # Don't fail on sqla error
            idtask = func2lock()
            self.assertEqual(idtask, None)

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

    def test_run(self):
        command.loop = False
        res = command.run(models)
        self.assertEqual(res, None)
        Task.create(func4test)
        res = command.run(models, kill=True)
        self.assertEqual(res, None)
        command.loop = True

        def f(*args, **kw):
            command.loop = False

        with patch('sqla_taskq.command._run', side_effect=f):
            res = command.run(models, kill=True)
            self.assertEqual(res, None)
        command.loop = True

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

            # No option in sqla_taskq section, we get the default
            config.add_section('sqla_taskq')
            res = command.parse_config_file('/fake')
            expected = {
                'kill': False,
                'timeout': 60,
            }
            self.assertEqual(res, expected)

            config.set('sqla_taskq', 'kill', 'true')
            config.set('sqla_taskq', 'timeout', '5')
            config.set('sqla_taskq', 'sqla_url', '//my_url')
            res = command.parse_config_file('/fake')
            expected = {
                'kill': True,
                'timeout': 5,
                'sqla_url': '//my_url',
            }
            self.assertEqual(res, expected)

    def test_parse_options(self):
        res = command.parse_options([])
        expected = {
            'kill': False,
            'sqla_url': None,
            'config_filename': None,
        }
        self.assertEqual(res, expected)

        res = command.parse_options([], parse_timeout=True)
        expected = {
            'kill': False,
            'sqla_url': None,
            'config_filename': None,
            'timeout': 60,
        }
        self.assertEqual(res, expected)

        options = ['-k', '-t', '90', '-u', 'sqlite://fake.db']
        res = command.parse_options(options, parse_timeout=True)
        expected = {
            'kill': True,
            'sqla_url': 'sqlite://fake.db',
            'config_filename': None,
            'timeout': 90,
        }
        self.assertEqual(res, expected)

        options = ['-k', '-t', '90',
                   '-u', 'sqlite://fake.db',
                   '-c', 'fake.ini']
        res = command.parse_options(options, parse_timeout=True)
        expected = {
            'kill': True,
            'sqla_url': 'sqlite://fake.db',
            'config_filename': 'fake.ini',
            'timeout': 90,
        }
        self.assertEqual(res, expected)

        config = ConfigParser.RawConfigParser()
        with patch('ConfigParser.ConfigParser', return_value=config):
            config.add_section('sqla_taskq')
            config.set('sqla_taskq', 'timeout', '5')
            res = command.parse_config_file('/fake')

            expected = {
                'kill': False,
                'timeout': 5,
            }
            self.assertEqual(res, expected)
