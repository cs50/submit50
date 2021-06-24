import contextlib
import filecmp
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from os.path import join
from unittest.mock import patch

from submit50 import submit
from submit50 import assignment


git_protocol = 'file://'

tests_dir = os.path.dirname(os.path.realpath(__file__))
tests_data_dir = join(tests_dir, 'data')

temp_dir = tempfile.mkdtemp()

os.environ['SUBMIT50_GIT_HOST'] = f'{git_protocol}{temp_dir}'

org_name = 'org'
org_dir = join(temp_dir, org_name)
os.mkdir(org_dir)

assignment_templates = ['assignment']
student_assignment_bare_repos = ['assignment-username']

@patch('builtins.input', return_value='y')
class TestSubmit50(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        unzip_assignment_templates()

    def setUp(self):
        unzip_student_assignment_bare_repos()

    def test_missing_git_cli(self, _):
        with patch('subprocess.check_output', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError,
                'It looks like git is not installed. Please install git then try again.'):
                with temp_student_cwd():
                    submit('org/assignment-user')

    def test_invalid_identifier_formats(self, _):
        invalid_identifiers = [
            '-',
            'invalid-uname',
            'invalid',
            'invalid-',
            'org/invalid',
            'org/invalid-',
            'org/-invalid',
            'org/-',
            'org/assignment-username-',
            'org/assignment-username_',
            'org/assignment-_username',
            'org/assignment-user_name',
        ]
        for identifier in invalid_identifiers:
            with self.assertRaisesRegex(ValueError, f'Invalid identifier "{identifier}"'):
                with temp_student_cwd():
                    submit(identifier)

    def test_missing_assignment_template(self, _):
        missing_assignment_template_dir = get_remote('missing')
        with self.assertRaisesRegex(RuntimeError,
            f'Failed to clone "{missing_assignment_template_dir}".'):
            with temp_student_cwd():
                submit('org/missing-username')

    def test_missing_assignment(self, _):
        assignment_template_name = 'assignment'
        student_assignment_name = f'{assignment_template_name}-missing'
        identifier = get_identifier(student_assignment_name)
        template_identifier = get_identifier(assignment_template_name)
        missing_assignment_remote = get_remote(f'{assignment_template_name}-missing')
        with self.assertRaisesRegex(RuntimeError, f'Failed to clone "{missing_assignment_remote}"'):
            with temp_student_cwd():
                submit(identifier)

    def test_dot_devcontainer_only(self, _):
        student_assignment = 'assignment-username'
        identifier = get_identifier(student_assignment)
        with temp_student_cwd('dot_devcontainer_only'):
            submit(identifier)
            self.assertCorrectSubmission('assignment-username', 'with_dotfiles')

    def test_dot_github_only(self, _):
        student_assignment = 'assignment-username'
        identifier = get_identifier(student_assignment)
        with temp_student_cwd('dot_github_only'):
            submit(identifier)
            self.assertCorrectSubmission(student_assignment, 'with_dotfiles')

    def test_add_delete_modify(self, _):
        student_assignment = 'assignment-username'
        identifier = get_identifier(student_assignment)
        with temp_student_cwd('add_delete_modify'):
            submit(identifier)
            self.assertCorrectSubmission(student_assignment, 'add_delete_modify')

    def test_no_confirm(self, input_mock):
        input_mock.return_value = 'no'
        with self.assertRaises(AssertionError):
            with temp_student_cwd():
                submit('org/assignment-username')

        input_mock.return_value = 'yes?'
        with self.assertRaises(AssertionError):
            with temp_student_cwd():
                submit('org/assignment-username')

        input_mock.return_value = 'yyes'
        with self.assertRaises(AssertionError):
            with temp_student_cwd():
                submit('org/assignment-username')

        input_mock.return_value = 'yesss'
        with self.assertRaises(AssertionError):
            with temp_student_cwd():
                submit('org/assignment-username')

    # TODO
    # def test_push_error(self):
    #     self.fail()

    def assertCorrectSubmission(self, student_assignment_name, correct_submission):
        with tempfile.TemporaryDirectory() as student_updated_clone_dir:
            student_assignment_bare_repo_dir = get_remote(student_assignment_name)
            subprocess.check_output([
                'git',
                'clone',
                '--quiet',
                student_assignment_bare_repo_dir,
                student_updated_clone_dir
            ])

            submission_dir = get_submission_path(correct_submission)
            self.assertEqualDirs(student_updated_clone_dir, submission_dir)

    def assertEqualDirs(self, a, b):
        diff = filecmp.dircmp(a, b)
        self.assertEqual(diff.left_only, [])
        self.assertEqual(diff.right_only, [])
        self.assertEqual(diff.diff_files, [])

def unzip_assignment_templates():
    assignment_templates_dir = pathlib.PosixPath(f'{tests_data_dir}/assignments/templates')
    for name in assignment_templates:
        zip_name = f'{name}.zip'
        zip_path = join(assignment_templates_dir, zip_name)
        dst = join(org_dir, name)
        unzip(zip_path, dst)

def unzip_student_assignment_bare_repos():
    student_assignment_bare_repos_dir = pathlib.PosixPath(
        f'{tests_data_dir}/assignments/student_assignment_bare_repos'
    )
    for name in student_assignment_bare_repos:
        zip_name = f'{name}.zip'
        zip_path = join(student_assignment_bare_repos_dir, zip_name)
        dst = join(org_dir, name)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        unzip(zip_path, dst)

def unzip(zip_path, dst):
    with zipfile.ZipFile(zip_path) as zip_file:
        zip_file.extractall(dst)

def get_assignment_template_path(name):
    return join(templates_dir, name)

def get_student_cwd_path(name):
    return join(tests_data_dir, 'student_cwd', name)

def get_submission_path(name):
    return join(tests_data_dir, 'submissions', name)

def get_remote(name):
    return f'{git_protocol}{org_dir}/{name}'

@contextlib.contextmanager
def temp_student_cwd(student_cwd=None):
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        if student_cwd is None:
            student_cwd_temp = temp_dir
        else:
            student_cwd_dir = get_student_cwd_path(student_cwd)
            student_cwd_temp = join(temp_dir, student_cwd)
            shutil.copytree(student_cwd_dir, student_cwd_temp)
        try:
            os.chdir(student_cwd_temp)
            yield student_cwd_temp
        finally:
            os.chdir(cwd)

def get_identifier(student_assignment):
    return f'{org_name}/{student_assignment}'
