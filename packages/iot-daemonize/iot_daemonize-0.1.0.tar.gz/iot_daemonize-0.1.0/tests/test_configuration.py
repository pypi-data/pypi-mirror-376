#!/usr/bin/env python
# -*- coding: utf-8 -*-

# general requirements
import unittest

import sys as _sys

# for the tests
from iot_daemonize import configuration


class ConfigurationArgumentTest(unittest.TestCase):
    def test_argument_empty(self):
        config = configuration.Configuration()
        config.add_config_arg('test')
        self.assertEqual({ 'action': None }, config._config_args['test'])

    def test_argument_default(self):
        config = configuration.Configuration()
        config.add_config_arg('test', default=1)
        self.assertEqual({ 'default': 1, 'action': None }, config._config_args['test'])
        config.add_config_arg('test', default='str')
        self.assertEqual({ 'default': 'str', 'action': None  }, config._config_args['test'])
        config.add_config_arg('test', default=1.09)
        self.assertEqual({ 'default': 1.09, 'action': None  }, config._config_args['test'])
        config.add_config_arg('test', default=True)
        self.assertEqual({ 'default': True, 'action': None  }, config._config_args['test'])

    def test_argument_help(self):
        config = configuration.Configuration()
        config.add_config_arg('test', help='test help')
        self.assertEqual({ 'help': 'test help', 'action': None  }, config._config_args['test'])

    def test_argument_action(self):
        config = configuration.Configuration()
        config.add_config_arg('test', action='store')
        self.assertEqual({ 'action': 'store' }, config._config_args['test'])
        config.add_config_arg('test', action='invalid')
        self.assertEqual({}, config._config_args['test'])

    def test_argument_flags(self):
        config = configuration.Configuration()
        config.add_config_arg('test', flags='-v')
        self.assertEqual({ 'flags': [ '-v' ], 'action': None  }, config._config_args['test'])
        config.add_config_arg('test', flags=['-v', '--verbose'])
        self.assertEqual({ 'flags': [ '-v', '--verbose' ], 'action': None  }, config._config_args['test'])

class ConfigurationArgumentParsingTest(unittest.TestCase):
    def test_argument_parser_init(self):
        config = configuration.Configuration()
        config.add_config_arg('test', flags='-v')
        self.assertEqual({ 'flags': [ '-v' ], 'action': None  }, config._config_args['test'])
        config._init_argument_parser()
        args = config._argument_parser.parse_args(['-v', '1'])
        self.assertEqual({ 'v': '1' }, vars(args))

    def test_argument_flags_parsing(self):
        config = configuration.Configuration()
        config.add_config_arg('test', flags='-v')
        self.assertEqual({ 'flags': [ '-v' ], 'action': None  }, config._config_args['test'])
        # this is a hack to modify the sys.argv used by the ArgumentParser as default
        _sys.argv[1:] = ['-v', '1']
        config.parse_args()
        self.assertEqual('1', config.test)
