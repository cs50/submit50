from .assignment import *
from .git import *


def submit(identifier):
    assert_git_installed()
    assignment = Assignment(identifier)
    assignment_template_client = AssignmentTemplateGitClient(identifier)
    with assignment_template_client.clone() as assignment_template_dir:
        copy_dotfiles_from(assignment_template_dir)
        student_assignment_client = StudentAssignmentGitClient(identifier)
        with student_assignment_client.clone_bare() as student_assignment_git_dir:
            student_assignment_client.submit()
