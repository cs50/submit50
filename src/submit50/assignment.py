import contextlib
import logging
import os
import re
import shutil
import tempfile

from .colors import yellow
from .git import AssignmentTemplateGitClient, StudentAssignmentGitClient
from .utils import copy, temp_student_cwd

class Assignment:
    def __init__(self, template_repo, username):
        self.template_repo = template_repo
        self.username = username
        self.student_repo = f'{template_repo}-{username}'
        self.dotfiles = ['.devcontainer', '.github', '.gitignore']

    def submit(self):
        self.confirm_files_to_submit()
        assignment_template_client = AssignmentTemplateGitClient(self.template_repo)
        logging.info('Fetching configurations ...')
        with assignment_template_client.clone() as assignment_template_dir:
            logging.info('Syncing configurations ...')
            with temp_student_cwd():
                self.copy_dotfiles_from(assignment_template_dir)
                logging.info('Uploading ...')
                student_assignment_client = StudentAssignmentGitClient(self.username, self.student_repo)
                with student_assignment_client.clone_bare():
                    student_assignment_client.add_commit_push()

    def copy_dotfiles_from(self, assignment_template_dir):
        """
        If the specified dotfiles exist in assignment_template_dir, removes these dotfiles from cwd,
        if they exist, and copies them from assignment_template_dir into cwd.

        :param assignment_template_dir: The path to the assignment template.
        """
        for dotfile in self.dotfiles:
            copy(assignment_template_dir, dotfile)

    def confirm_files_to_submit(self):
        self.list_cwd()
        try:
            answer = input(yellow(
                ("Keeping in mind the course's policy on academic honesty,"
                 ' are you sure you want to submit these files (yes/no)? ')
            ))
        except EOFError:
            answer = ''
        assert re.fullmatch(r'(?:y|yes)', answer.strip(), re.I), 'Cancelled.'

    # TODO factor out and refactor
    # TODO use something other than os.walk to ignore listing ignored files/dirs?
    def list_cwd(self):
        contents = list(os.walk(os.getcwd()))
        if len(contents) < 1:
            raise RuntimeError('No files to submit.')

        ignored_entries = [*self.dotfiles, '.git']
        indentation_level = 2
        output = []
        root, dirs, files = contents[0]
        for f in files:
            if f in ignored_entries:
                continue
            output.append('{}{}'.format(' ' * indentation_level, f))

        for root, dirs, files in contents[1:]:
            relative_path = root.replace(os.getcwd(), '')
            if any(relative_path.lstrip('/').startswith(dotfile) for dotfile in ignored_entries):
                continue
            basename = os.path.basename(root)
            level = relative_path.count(os.sep)
            indent = ' ' * indentation_level * level
            output.append(f'{indent}{basename}/')
            subindent = ' ' * indentation_level * (level + 1)
            for f in files:
                output.append(f'{subindent}{f}')

        if len(output) < 1:
            raise RuntimeError('No files to submit.')

        logging.info(yellow('Files that will be submitted:'))
        for entry in output:
            logging.info(entry)
