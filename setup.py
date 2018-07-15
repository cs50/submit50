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
    cmdclass=cmdclass,
    message_extractors = {
        'submit50': [('**.py', 'python', None),],
    },
    description="This is submit50, CS50's internal library for using GitHub as data storage.",
    install_requires=["babel", "push50", "requests", "termcolor"],
    keywords=["submit", "submit50"],
    name="submit50",
    python_requires=">= 3.6",
    packages=["submit50"],
    url="https://github.com/cs50/submit50",
    version="1.0.0",
    include_package_data=True
)
