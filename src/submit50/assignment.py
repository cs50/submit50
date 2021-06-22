import os
import re

from os.path import exists, join
from shutil import copy, copytree, rmtree

DOTFILES = ['.devcontainer', '.github', '.gitignore']

# E.g., org/assignment-username, org/assignment-1-username
# GitHub usernames and org names can only contain alphanumeric chars and one hyphen and cannot
# start or end with a hyphen
IDENTIFIER_PATTERN = re.compile(
    '[A-Za-z0-9]+(?:-?[A-Za-z0-9]+)/[A-Za-z0-9\.\-_]+-[A-Za-z0-9]+(?:-?[A-Za-z0-9]+)?')

def assert_valid_identifier_format(identifier):
    if IDENTIFIER_PATTERN.fullmatch(identifier) is None:
        raise ValueError(f'Invalid identifier "{identifier}".')

def assignment_name_from_remote(remote):
    """
    Extracts the name of the assignment from the URL of the student's copy and returns it. For
    example, if the URL of the student's copy is https://github.com/org/assignment-username,
    returns org/assignment.

    :param remote: The URL of the student's copy of the assignment
    """
    identifier = identifier_from_remote(remote)
    assignment_name = assignment_name_from_identifier(identifier)
    return assignment_name

def identifier_from_remote(remote):
    return '/'.join(remote.rsplit('/', 2)[1:])

def assignment_name_from_identifier(identifier):
    """
    Extracts the name of the assignment from the name of the student's copy and returns it. For
    example, if the student's copy is org/assignment-username, returns org/assignment.

    :param identifer: The name of the student's copy of the assignment (E.g.,
        org/assignment-username)
    """
    assignment_name, _ = identifier.rsplit('-', 1)
    return assignment_name

def copy_dotfiles_from(assignment_template_dir):
    """
    If the specified dotfiles exist in assignment_template_dir, removes these dotfiles from cwd, if
    they exist, and copies them from assignment_template_dir into cwd.

    :param assignment_template_dir: The path to the assignment template.
    """
    for dotfile in DOTFILES:
        copy_dotfile(assignment_template_dir, dotfile)

def copy_dotfile(assignment_template_dir, dotfile):
    """
    If dotfile exist in assignment_template_dir, removes dotfile from cwd, if it exists, and copies it
    from assignment_template_dir into cwd.

    :param assignment_template_dir: The path to the assigment template.
    """
    src = join(assignment_template_dir, dotfile)
    if exists(src):
        # TODO warn before removing if file or directory is different
        remove_if_exists(dotfile)
        try:
            copytree(src, join(os.getcwd(), dotfile))
        except NotADirectoryError:
            copy(src, join(os.getcwd(), dotfile))

        # TODO handle other potential copying issues

def remove_if_exists(path):
    """
    Removes a file or a directory from cwd if it exists.

    :param path The path of the file or directory to be removed from cwd.
    """
    # TODO is this a portable way for referencing cwd?
    path = join('.', path)
    if exists(path):
        try:
            rmtree(path)
        except NotADirectoryError:
            os.remove(path)
