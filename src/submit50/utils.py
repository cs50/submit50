import contextlib
import logging
import os
import shutil
import tempfile


def copy(parent_dir, entry):
    """
    If entry exists in parent_dir, removes entry from cwd, if it exists, then copies entry from
    parent_dir into cwd. entry has the same name in cwd after it's copied.

    :param parent_dir: the parent directory of the entry to be copied
    :param entry: the file or directory to be copied from parent_dir into cwd
    """
    src = os.path.join(parent_dir, entry)
    if os.path.exists(src):
        remove_if_exists(entry)
        try:
            shutil.copytree(src, os.path.join(os.getcwd(), entry))
        except NotADirectoryError as exc:
            logging.debug(exc, exc_info=True)
            shutil.copy(src, os.path.join(os.getcwd(), entry))

        # TODO handle other potential copying issues

def remove_if_exists(path):
    """
    Removes a file or a directory from cwd if it exists.

    :param path The path of the file or directory to be removed from cwd.
    """
    path = os.path.join(os.getcwd(), path)
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
        except NotADirectoryError as exc:
            logging.debug(exc, exc_info=True)
            os.remove(path)

@contextlib.contextmanager
def temp_student_cwd():
    """
    A context manager that copies the contents of cwd into a temp directory. This should be used to
    avoid performing any potentially destructive operations in student's cwd (e.g., replacing a
    configuration directory by one from the distro).
    """
    # TODO only copy files that are not ignored
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_cwd = os.path.join(temp_dir, 'temp_cwd')
        shutil.copytree(cwd, temp_cwd)
        try:
            os.chdir(temp_cwd)
            yield temp_cwd
        finally:
            os.chdir(cwd)
