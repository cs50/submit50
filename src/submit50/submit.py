from .assignment import *
from .git import *


def submit(identifier):
    GitRepo.assert_git_installed()
    assignment = Assignment(identifier)
    assignment_template_dir = clone_assignment_template(identifier)
    copy_dotfiles_from(assignment_template_dir)
    clone_add_commit_push(identifier)
