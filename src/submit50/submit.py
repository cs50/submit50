from .assignment import *
from .git import *


def submit(identifier):
    assert_git_installed()
    assignment = Assignment(identifier)
    assignment.submit()
