[![Build Status](https://travis-ci.org/cs50/submit50.svg?branch=master)](https://travis-ci.org/cs50/submit50)

# TODO

* Client
    * Remove tag once handled by server.
* Server
    * Tag latest commit.
    * Release latest commit.
    * Update default branch.

# CHANGELOG

* 2.1.4
    * Fix problem with two-factor authentication.
    * Avoid printing "Submission cancelled" when it's inappropriate.
* 2.1.3
    * Canonicalizd username after login to allow login via email.
    * Generalized finding path to python3.
* 2.1.2
    * Added more error handling to `submit50 --checkout`.
    * Updated messages displayed to user to direct them to CS50.me.
* 2.1.1
    * Suppressed student compile flags while installing getch.
* 2.1.0
    * TBD
* 2.0.0
    * Ported to Python.
    * Added support for two-factor authentication.
    * Added course identifier as prefix to branches and tags.
    * Added support for --checkout of specific usernames.
    * Hid diagnostic output unless --verbose flag is used.
    * Added check for version file.
* 1.1.0
    * Added support for expecting and ignoring files.
    * Added support for logging in via email address.
    * Added check for whether problem exists.
    * Fixed bugs whereby spaces or dollar signs in usernames broke login.
    * Fixed bug whereby pushes would fail if email address not yet confirmed.
* 1.0.3
    * Initial commit.
