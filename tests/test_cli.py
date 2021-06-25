import imp
import os
import sys
import unittest

from unittest.mock import patch


tests_dir = os.path.dirname(os.path.realpath(__file__))
cli = imp.load_source('cli', os.path.join(tests_dir, '..', 'bin', 'submit50'))

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
