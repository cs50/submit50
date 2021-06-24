import contextlib
import os
import subprocess
import tempfile

from os.path import join

# TODO log outputs in verbose mode

GIT_HOST = 'https://github.com/'

class GitClient:
    def __init__(self, repo, git_host=None):
        self.git_host = os.getenv('SUBMIT50_GIT_HOST', GIT_HOST)
        self.repo = repo
        self.git_dir = None

class AssignmentTemplateGitClient(GitClient):
    @contextlib.contextmanager
    def clone(self):
        """
        Clones assignment template into a temporary directory.

        :param identifer: The name of the student's copy of the assignment (E.g.,
            org/assignment-username)
        """
        remote = join(self.git_host, self.repo)
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                clone(['--depth', '1', '--quiet', remote, temp_dir])
            except subprocess.CalledProcessError:
                raise RuntimeError(f'Failed to clone "{remote}".')
            yield temp_dir

class StudentAssignmentGitClient(GitClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configs = StudentAssignmentGitClient._default_configs()

    @contextlib.contextmanager
    def clone_bare(self):
        remote = join(self.git_host, self.repo)
        with tempfile.TemporaryDirectory() as git_dir:
            try:
                self._clone(['--bare', '--quiet', remote, git_dir])
            except subprocess.CalledProcessError:
                raise RuntimeError(f'Failed to clone "{remote}".')
            self.git_dir = git_dir
            yield git_dir

    def add_commit_push(self):
        try:
            self._add_all()
            self._commit()
            self._push()
        except subprocess.CalledProcessError as ex:
            raise RuntimeError('Failed to submit.')

    def _clone(self, args):
        return self._git(['clone', *args])

    def _add_all(self):
        return self._git(['add', '--all'])

    def _commit(self):
        return self._git(['commit', '--message', 'Automated commit by submit50'])

    def _push(self):
        current_branch = self._current_branch()
        return self._git(['push', '--quiet', 'origin', current_branch])

    def _current_branch(self):
        return self._git(['branch', '--show-current']).decode().rstrip()

    def _git(self, args):
        git_dir = ['--git-dir', self.git_dir] if self.git_dir else []
        return git([*git_dir, '--work-tree', os.getcwd(), *self.configs, *args])

    @staticmethod
    def _default_configs():
        configs = []
        if user_name_not_configured():
            configs.extend(['-c', 'user.name=submit50'])

        if user_email_not_configured():
            configs.extend(['-c', 'user.email=submit50@users.noreply.github.com'])

        if credential_helper_not_configured():
            configs.extend(['-c', 'credential.helper=cache'])

        return configs

def assert_git_installed():
    """
    Ensures that git is installed and on PATH and raises a RuntimeError if not.
    """
    try:
        git(['--version'])
    except FileNotFoundError:
        raise RuntimeError('It looks like git is not installed. Please install git then try again.')

def clone(args):
    return git(['clone', *args])

def user_name_not_configured():
    return not_configured('user.name')

def user_email_not_configured():
    return not_configured('user.email')

def credential_helper_not_configured():
    return not_configured('credential.helper')

def not_configured(key):
    try:
        return config(['--get', key])
    except subprocess.CalledProcessError:
        return True

    return False

def config(args):
    return git(['config', *args])

def git(args):
    return subprocess.check_output(['git', *args])
