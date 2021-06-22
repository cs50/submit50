import os
import subprocess

from os.path import join
from tempfile import mkdtemp

from .assignment import assignment_name_from_identifier, assignment_name_from_remote

GIT_HOST = os.getenv('SUBMIT50_GIT_HOST', 'https://github.com')

# TODO log outputs in verbose mode

def assert_git_installed():
    """
    Ensures that git is installed and on PATH and raises a RuntimeError if not.
    """
    try:
        subprocess.run(['git', '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        raise RuntimeError('It looks like git is not installed. Please install git then try again.')

def clone_assignment_template(identifier):
    """
    Clones assignment template into a temporary directory.

    :param identifer: The name of the student's copy of the assignment (E.g.,
        org/assignment-username)
    """
    assignment_name = assignment_name_from_identifier(identifier)
    remote = join(GIT_HOST, assignment_name)
    assignment_temp_path = _clone_assignment_template_in_temp_dir(remote)
    return assignment_temp_path

def _clone_assignment_template_in_temp_dir(remote):
    temp_path = mkdtemp()
    try:
        subprocess.check_output(['git', 'clone', '--depth', '1', '--quiet', remote, temp_path])
    except subprocess.CalledProcessError:
        raise RuntimeError(f'Failed to clone "{remote}".')
    return temp_path

def clone_student_assignment_bare(identifier):
    remote = join(GIT_HOST, identifier)
    assignment_bare_path = _clone_student_assignment_bare_in_temp_dir(remote)
    return assignment_bare_path

def _clone_student_assignment_bare_in_temp_dir(remote):
    temp_path = mkdtemp()
    try:
        subprocess.check_output(['git', 'clone', '--bare', '--quiet', remote, temp_path])
    except subprocess.CalledProcessError:
        assignment_name = assignment_name_from_remote(remote)
        raise RuntimeError(
            f'Failed to clone "{remote}". Did you accept assignment "{assignment_name}"?')
    return temp_path

def clone_add_commit_push(identifier):
    git_dir = clone_student_assignment_bare(identifier)
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
