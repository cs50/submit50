import importlib
import os
import sys
import unittest

from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader
from unittest.mock import patch


tests_dir = os.path.dirname(os.path.realpath(__file__))

spec = spec_from_loader(
    'cli',
    SourceFileLoader('cli', os.path.join(tests_dir, '..', 'bin', 'submit50'))
)
cli = module_from_spec(spec)
sys.modules['cli'] = cli
spec.loader.exec_module(cli)

@patch('cli.configure_logging')
@patch('cli.submit')
class TestCLI(unittest.TestCase):
    def test_invalid_args(self, submit_mock, configure_logging_mock):
        with patch.object(sys, 'argv', ['submit50']):
            with self.assertRaises(SystemExit):
                cli.main()

        with patch.object(sys, 'argv', ['submit50', 'org/assignment']):
            with self.assertRaises(SystemExit):
                cli.main()

        with patch.object(sys, 'argv', ['submit50', 'org/assignment', 'username', 'extra']):
            with self.assertRaises(SystemExit):
                cli.main()

    def test_valid_args(self, submit_mock, configure_logging_mock):
        with patch.object(sys, 'argv', ['submit50', 'org/assignment', 'username']):
            cli.main()
            submit_mock.assert_called_once_with('org/assignment', 'username')
