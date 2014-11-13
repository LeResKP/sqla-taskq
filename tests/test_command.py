import unittest
from mock import patch, Mock
import ConfigParser
from taskq import command


class TestCommand(unittest.TestCase):

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
