if __import__("os").name == "nt":
    raise RuntimeError("submit50 does not support Windows directly. Instead, you should install the Windows Subsystem for Linux (https://docs.microsoft.com/en-us/windows/wsl/install-win10) and then install submit50 within that.")

from setuptools import setup
setup(
    author="CS50",
    author_email="sysadmins@cs50.harvard.edu",
    classifiers=[
        "Intended Audience :: Education",
        "Programming Language :: Python :: 3",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
    message_extractors = {
        'submit50': [('**.py', 'python', None),],
    },
    description="This is submit50, with which you can submit solutions to problems for CS50.",
    install_requires=["lib50>=3,<4", "requests>=2.19", "termcolor>=1.1"],
    keywords=["submit", "submit50"],
    name="submit50",
    python_requires=">=3.6",
    license="GPLv3",
    packages=["submit50"],
    url="https://github.com/cs50/submit50",
    entry_points={
        "console_scripts": ["submit50=submit50.__main__:main"]
    },
    version="3.1.0",
    include_package_data=True
)
