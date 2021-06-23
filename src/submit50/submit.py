from .assignment import *
from .git import *


def submit(identifier):
    GitRepo.assert_git_installed()
    assert_valid_identifier_format(identifier)
    assignment_template_dir = clone_assignment_template(identifier)
    copy_dotfiles_from(assignment_template_dir)
    clone_add_commit_push(identifier)
