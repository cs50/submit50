import logging
import re
import sys

from .colors import yellow, red
from .git import AssignmentTemplateGitClient, StudentAssignmentGitClient
from .utils import copy, temp_student_cwd

class Assignment:
    def __init__(self, template_repo, username):
        self.template_repo = template_repo
        self.username = username
        self.student_repo = f'{template_repo}-{username}'
        self.dotfiles = ['.github', '.gitignore']
        self.no_list_prefixes = [
            *self.dotfiles,
            '.devcontainer',
            '.venv',
            '.vscode',
            'node_modules',
        ]

    def submit(self):
        assignment_template_client = AssignmentTemplateGitClient(self.template_repo)
        logging.info('Preparing files ...')
        with assignment_template_client.clone() as assignment_template_dir:
            with temp_student_cwd():
                self.copy_dotfiles_from(assignment_template_dir)
                student_assignment_client = StudentAssignmentGitClient(self.username, self.student_repo)
                with student_assignment_client.clone_bare():
                    files_to_submit = student_assignment_client.add()
                    self.confirm_files_to_submit(files_to_submit)
                    logging.info('Uploading ...')
                    student_assignment_client.commit_push()

    def copy_dotfiles_from(self, assignment_template_dir):
        """
        If the specified dotfiles exist in assignment_template_dir, removes these dotfiles from cwd,
        if they exist, and copies them from assignment_template_dir into cwd.

        :param assignment_template_dir: The path to the assignment template.
        """
        for dotfile in self.dotfiles:
            copy(assignment_template_dir, dotfile)

    def confirm_files_to_submit(self, files_to_submit):
        self.list_files_to_submit(files_to_submit)
        try:
            answer = input(yellow(
                ("Keeping in mind the course's policy on academic honesty,"
                 ' are you sure you want to submit these files (yes/no)? ')
            ))
        except EOFError:
            answer = ''
        assert re.fullmatch(r'(?:y|yes)', answer.strip(), re.I), 'Cancelled.'

    def list_files_to_submit(self, files_to_submit):
        user_files = []
        for entry in files_to_submit:
            if self.should_list(entry):
                user_files.append(entry)
        
        if len(user_files) == 0:
            print(red("Empty submission detected, abort.\nPlease make sure you are not in an empty directory, or your gitignore configuration does not result in an empty submission."))
            sys.exit(1)
        else:
            logging.info('Files that will be submitted: ')
            for entry in user_files:
                logging.info(yellow(f'  {entry}'))

    def should_list(self, entry):
        return all(not entry.startswith(prefix) for prefix in self.no_list_prefixes)
