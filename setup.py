from os.path import isfile
from setuptools import setup
from setuptools.command.install import install
from subprocess import call
from sys import platform, version_info

class Certs(install):
    def run(self):
        install.run(self)
        if platform == "darwin" and version_info >= (3, 6):
            INSTALL_CERTS = "/Applications/Python 3.6/Install Certificates.command"
            if not isfile(INSTALL_CERTS) or call(INSTALL_CERTS) != 0:
                raise Error("Error installing certificates.")

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    description="This is submit50, with which you can submit solutions to problems for CS50.",
    install_requires=["backports.shutil_get_terminal_size", "backports.shutil_which", "pexpect>=4.0", "requests", "six", "termcolor"],
    keywords=["submit", "submit50"],
    name="submit50",
    py_modules=["submit50"],
    cmdclass={"install": Certs},
    entry_points={
        "console_scripts": ["submit50=submit50:main"]
    },
    url="https://github.com/cs50/submit50",
    version="2.3.0"
)
