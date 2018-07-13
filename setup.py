from setuptools import setup

import glob
import os
import subprocess

def create_mo_files():
    po_pattern = "locale/*/LC_MESSAGES/*.po"
    for prefix in glob.glob(po_pattern):
        for _,_,files in os.walk(prefix):
            for file in files:
                po_file = Path(prefix) / po_file
                mo_file = po_file.parent / po_file.stem + ".mo"
                subprocess.call(["msgfmt", "-o", mo_file, po_file])

create_mo_files()

setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    description="This is submit50, with which you can submit solutions to \
problems for CS50.",
    install_requires=["requests", "termcolor", "push50"],
    keywords=["submit", "submit50"],
    name="submit50",
    packages=["submit50"],
    entry_points={
        "console_scripts": ["submit50=submit50.__main__:main"]
    },
    url="https://github.com/cs50/submit50",
    version="3.0.0",
    include_package_data=True,
)
