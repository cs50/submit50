from .assignment import *
from .git import *


def submit(identifier):
    Git.assert_git_installed()
    assignment = Assignment(identifier)
    assignment_template_client = Git(identifier)
    with assignment_template_client.clone_assignment_template() as assignment_template_dir:
        copy_dotfiles_from(assignment_template_dir)
        student_assignment_client = Git(identifier)
        with student_assignment_client.clone_student_assignment_bare() as student_assignment_git_dir:
            add_commit_push(student_assignment_git_dir)
