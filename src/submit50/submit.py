from .assignment import Assignment
from .git import assert_git_installed


def submit(identifier):
    assert_git_installed()
    assignment = Assignment(identifier)
    assignment.submit()
