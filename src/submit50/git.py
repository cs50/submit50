import contextlib
import os
import subprocess
import tempfile

from os.path import join
from tempfile import mkdtemp

from .assignment import assignment_name_from_identifier, assignment_name_from_remote


# TODO log outputs in verbose mode

class Git:
    def __init__(self, identifier, git_host=os.getenv('SUBMIT50_GIT_HOST', 'https://github.com/')):
        self.git_host = git_host
        self.identifier = identifier

    @staticmethod
    def assert_git_installed():
        """
        Ensures that git is installed and on PATH and raises a RuntimeError if not.
        """
        try:
            subprocess.check_output(['git', '--version'])
        except FileNotFoundError:
            raise RuntimeError('It looks like git is not installed. Please install git then try again.')

    @contextlib.contextmanager
    def clone_assignment_template(self):
        """
        Clones assignment template into a temporary directory.

        :param identifer: The name of the student's copy of the assignment (E.g.,
            org/assignment-username)
        """
        assignment_name = assignment_name_from_identifier(self.identifier)
        remote = join(self.git_host, assignment_name)
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                subprocess.check_output(
                    ['git', 'clone', '--depth', '1', '--quiet', remote, temp_dir]
                )
            except subprocess.CalledProcessError:
                raise RuntimeError(f'Failed to clone "{remote}".')
            yield temp_dir

    @contextlib.contextmanager
    def clone_student_assignment_bare(self):
        remote = join(self.git_host, self.identifier)
        with tempfile.TemporaryDirectory() as git_dir:
            try:
                subprocess.check_output(['git', 'clone', '--bare', '--quiet', remote, git_dir])
            except subprocess.CalledProcessError:
                assignment_name = assignment_name_from_remote(remote)
                raise RuntimeError(
                    f'Failed to clone "{remote}". Did you accept assignment "{assignment_name}"?')
            self.git_dir = git_dir
            yield git_dir

    def enable_credential_cache(self):
        """
        Configures git credential cache helper if no credential helper is configured. The cache
        helper stores credentials in memory for 15 minutes after the user provides them.
        """
        if not self._git(['config', 'credential.helper']):
            self._git(['config', 'credential.helper', 'cache'])

    def _git(self, args):
        return subprocess.check_output(['git'] + args, env=self.env)

def add_commit_push(git_dir):
    try:
        env = os.environ.copy()
        env['GIT_DIR'] = git_dir
        env['GIT_WORK_TREE'] = os.getcwd()

        subprocess.check_output(['git', 'add', '--all'], env=env)
        subprocess.check_output(
            ['git', 'commit', '--message', 'Automatic commit by submit50'],
            env=env
        )
        subprocess.check_output(
            'git push --quiet origin $(git branch --show-current)',
            shell=True,
            env=env
        )
    except subprocess.CalledProcessError as ex:
        raise RuntimeError('Failed to submit.')
