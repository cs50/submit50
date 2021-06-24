import os
import re

from os.path import exists, join
from shutil import copy, copytree, rmtree

from .git import AssignmentTemplateGitClient, StudentAssignmentGitClient

class Assignment:
    def __init__(self, identifier):
        self.identifier = identifier

        # E.g., org/assignment-username, org/assignment-1-username
        # GitHub usernames and org names can only contain alphanumeric chars and one hyphen and cannot
        # start or end with a hyphen
        self.identifier_pattern = re.compile(
            '[A-Za-z0-9]+(?:-?[A-Za-z0-9]+)/[A-Za-z0-9\.\-_]+-[A-Za-z0-9]+(?:-?[A-Za-z0-9]+)?'
        )
        self.assert_valid_identifier_format()

        self.dotfiles = ['.devcontainer', '.github', '.gitignore']

    def assert_valid_identifier_format(self):
        if self.identifier_pattern.fullmatch(self.identifier) is None:
            raise ValueError(f'Invalid identifier "{self.identifier}".')

    def submit(self):
        assignment_template_repo = self.assignment_template_repo()
        assignment_template_client = AssignmentTemplateGitClient(assignment_template_repo)
        with assignment_template_client.clone() as assignment_template_dir:
            self.copy_dotfiles_from(assignment_template_dir)
            student_assignment_client = StudentAssignmentGitClient(self.identifier)
            with student_assignment_client.clone_bare() as student_assignment_git_dir:
                student_assignment_client.add_commit_push()

    def assignment_template_repo(self):
        """
        Extracts the name of the assignment from the name of the student's copy and returns it. For
        example, if the student's copy is org/assignment-username, returns org/assignment.

        :param identifer: The name of the student's copy of the assignment (E.g.,
            org/assignment-username)
        """
        assignment_name, _ = self.identifier.rsplit('-', 1)
        return assignment_name

    def copy_dotfiles_from(self, assignment_template_dir):
        """
        If the specified dotfiles exist in assignment_template_dir, removes these dotfiles from cwd, if
        they exist, and copies them from assignment_template_dir into cwd.

        :param assignment_template_dir: The path to the assignment template.
        """
        for dotfile in self.dotfiles:
            self.copy_dotfile(assignment_template_dir, dotfile)

    def copy_dotfile(self, assignment_template_dir, dotfile):
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
