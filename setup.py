from setuptools import setup

import glob
import os
import subprocess

def create_mo_files():
    """Compiles .po files in local/LANG to .mo files and returns them as array of data_files"""

    mo_files=[]
    for prefix in glob.glob("locale/*/LC_MESSAGES"):
        for _,_,files in os.walk(prefix):
            for file in files:
                if file.endswith(".po"):
                    po_file = os.path.join(prefix, file)
                    mo_file = os.path.splitext(po_file)[0] + ".mo"
                    subprocess.call(["msgfmt", "-o", mo_file, po_file])
                    mo_files.append((os.path.join("submit50", prefix), [mo_file]))
    return mo_files

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
    install_requires=["pexpect>=4.0", "requests", "termcolor"],
    keywords=["submit", "submit50"],
    name="submit50",
    py_modules=["submit50"],
    entry_points={
        "console_scripts": ["submit50=submit50:main"]
    },
    data_files=create_mo_files(),
    url="https://github.com/cs50/submit50",
    version="2.4.9"
)
