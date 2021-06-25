from .assignment import Assignment
from .git import assert_git_installed

def submit(assignment, username):
    assert_git_installed()
    assignment = Assignment(assignment, username)
    assignment.submit()
