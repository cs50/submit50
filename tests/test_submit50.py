import filecmp
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from os.path import join
from unittest.mock import patch


git_protocol = 'file://'

tests_dir = os.path.dirname(os.path.realpath(__file__))
tests_data_dir = join(tests_dir, 'data')

temp_dir = join(tempfile.gettempdir(), 'submit50_tests')
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.mkdir(temp_dir)

os.environ['SUBMIT50_GIT_HOST'] = f'{git_protocol}{temp_dir}'

from submit50 import submit

org_name = 'org'
org_dir = join(temp_dir, org_name)
os.mkdir(org_dir)

assignment_template_name = 'assignment'
assignment_template_dir = join(org_dir, assignment_template_name)
assignment_template_zip_path = join(tests_data_dir, 'assignments', 'templates', 'assignment.zip')
with zipfile.ZipFile(assignment_template_zip_path) as zip_file:
    zip_file.extractall(assignment_template_dir)

student_assignment_name = 'assignment-username'
student_assignment_bare_repo_dir = join(org_dir, student_assignment_name)
student_assignment_bare_repo_zip_path = join(
    tests_dir,
    'data',
    'assignments',
    'student_assignment_bare_repos',
    'assignment-username.zip'
)

class TestSubmit50(unittest.TestCase):
    def test_missing_git_cli(self):
        with patch('subprocess.run', side_effect=FileNotFoundError):
            with self.assertRaisesRegex(RuntimeError,
                'It looks like git is not installed. Please install git then try again.'):
                submit('org/assignment-user')

    def test_invalid_identifier_formats(self):
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
                submit(identifier)

    def test_missing_assignment_template(self):
        missing_assignment_template_dir = f'{git_protocol}{org_dir}/missing'
        with self.assertRaisesRegex(RuntimeError,
            f'Failed to clone "{missing_assignment_template_dir}".'):
            submit('org/missing-username')

    def test_missing_assignment(self):
        student_assignment_name = f'{assignment_template_name}-missing'
        identifier = f'{org_name}/{student_assignment_name}'
        missing_assignment_bare = f'{git_protocol}{org_dir}/{assignment_template_name}-missing'
        with self.assertRaisesRegex(RuntimeError,
            (f'Failed to clone "{missing_assignment_bare}". Did you accept assignment'
             f' "{org_name}/{assignment_template_name}"?')):
            submit(identifier)

    def test_dot_devcontainer_only(self):
        reset_student_assignment_bare_repo()
        cwd = os.getcwd()
        student_cwd = join(tests_data_dir, 'student_cwd', 'dot_devcontainer_only')
        with tempfile.TemporaryDirectory() as temp_dir:
            student_cwd_temp = join(temp_dir, 'dot_devcontainer_only')
            shutil.copytree(student_cwd, student_cwd_temp)
            try:
                os.chdir(student_cwd_temp)
                submit('org/assignment-username')
            finally:
                os.chdir(cwd)

            submission_dir = join(tests_data_dir, 'submissions', 'with_dotfiles')
            student_updated_clone_dir = join(temp_dir, 'student_updated_clone')
            subprocess.check_output(
                ['git', 'clone', student_assignment_bare_repo_dir, student_updated_clone_dir]
            )
            self.assertEqualDirs(student_updated_clone_dir, submission_dir)

    def test_dot_github_only(self):
        reset_student_assignment_bare_repo()
        cwd = os.getcwd()
        student_cwd = join(tests_data_dir, 'student_cwd', 'dot_github_only')
        with tempfile.TemporaryDirectory() as temp_dir:
            student_cwd_temp = join(temp_dir, 'dot_github_only')
            shutil.copytree(student_cwd, student_cwd_temp)
            try:
                os.chdir(student_cwd_temp)
                submit('org/assignment-username')
            finally:
                os.chdir(cwd)

            submission_dir = join(tests_data_dir, 'submissions', 'with_dotfiles')
            student_updated_clone_dir = join(temp_dir, 'student_updated_clone')
            subprocess.check_output(
                ['git', 'clone', student_assignment_bare_repo_dir, student_updated_clone_dir]
            )
            self.assertEqualDirs(student_updated_clone_dir, submission_dir)

    def test_add_delete_modify(self):
        reset_student_assignment_bare_repo()
        cwd = os.getcwd()
        student_cwd = join(tests_data_dir, 'student_cwd', 'add_delete_modify')
        with tempfile.TemporaryDirectory() as temp_dir:
            student_cwd_temp = join(temp_dir, 'add_delete_modify')
            shutil.copytree(student_cwd, student_cwd_temp)
            try:
                os.chdir(student_cwd_temp)
                submit('org/assignment-username')
            finally:
                os.chdir(cwd)

            submission_dir = join(tests_data_dir, 'submissions', 'add_delete_modify')
            student_updated_clone_dir = join(temp_dir, 'student_updated_clone')
            subprocess.check_output(
                ['git', 'clone', student_assignment_bare_repo_dir, student_updated_clone_dir]
            )
            self.assertEqualDirs(student_updated_clone_dir, submission_dir)

    # TODO
    # def test_push_error(self):
    #     self.fail()

    def assertEqualDirs(self, a, b):
        diff = filecmp.dircmp(a, b)
        self.assertEqual(diff.left_only, [])
        self.assertEqual(diff.right_only, [])
        self.assertEqual(diff.diff_files, [])

def reset_student_assignment_bare_repo():
    if os.path.exists(student_assignment_bare_repo_dir):
        shutil.rmtree(student_assignment_bare_repo_dir)

    with zipfile.ZipFile(student_assignment_bare_repo_zip_path) as zip_file:
        zip_file.extractall(student_assignment_bare_repo_dir)
