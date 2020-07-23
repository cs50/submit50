import contextlib
import functools
import io
import logging
import os
import pathlib
import requests
import tempfile
import re
import subprocess
import sys
import time
import threading
import unittest

from http import server

import submit50.__main__ as submit50

class TestSubmit50_Status(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.PORT = 8000
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = pathlib.Path(self.temp_dir.name)
        self.sub_dir = self.temp_path / "status/submit50"
        os.makedirs(self.sub_dir)

        Handler = functools.partial(server.SimpleHTTPRequestHandler, directory=self.temp_path)
        self.httpd = server.HTTPServer(("localhost", self.PORT), Handler)

    @classmethod
    def tearDownClass(self):
        self.temp_dir.cleanup()
        submit50.SUBMIT_URL = "https://submit.cs50.io"

    @classmethod
    def httpd_serve(self, times):
        """Serve the given number (times) of requests. Shuts down after."""
        for i in range(times):
            self.httpd.handle_request()

    def test_bad_server(self):
        submit50.SUBMIT_URL = "https://foobar.cs50.io"
        with self.assertRaises(requests.exceptions.ConnectionError):
            submit50.check_announcements()

    def test_message(self):
        submit50.SUBMIT_URL = f"http://localhost:{self.PORT}"

        with open(self.sub_dir / "index.html", "w") as f:
            f.write("A message here\n")

        t = threading.Thread(None, self.httpd_serve, args=[2])
        t.start()
        
        with self.assertRaisesRegex(submit50.Error, "A message here"):
            submit50.check_announcements()

    def test_no_message(self):
        submit50.SUBMIT_URL = f"http://localhost:{self.PORT}"

        with open(self.sub_dir / "index.html", "w") as f:
            f.write("")

        t = threading.Thread(None, self.httpd_serve, args=[2])
        t.start()
        
        self.assertIsNone(submit50.check_announcements())


class TestSubmit50_Version(unittest.TestCase):
    def test_bad_server(self):
        submit50.SUBMIT_URL = "https://submit.cs50.io/404dne"

        with self.assertRaisesRegex(submit50.Error, ".*unknown.*"):
            submit50.check_version()

    def test_old_version(self):
        submit50.SUBMIT_URL = "https://submit.cs50.io"
        submit50.__version__ = "0.0.0"

        with self.assertRaisesRegex(submit50.Error, ".*outdated.*"):
            submit50.check_version()


class TestSubmit50_Prompt(unittest.TestCase):
    @contextlib.contextmanager
    def replace_stdin(self):
        old = sys.stdin
        try:
            with io.StringIO() as stdin_s:
                sys.stdin = stdin_s
                sys.stdin.buffer = sys.stdin
                yield sys.stdin
        finally:
            sys.stdin = old

    def test_no_files(self):
        with self.assertRaisesRegex(submit50.Error, ".*No files.*"):
            submit50.prompt(False, [], [])

    def test_exclude_files(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.assertTrue(submit50.prompt(False, ["foo.c"], ["bar.c"]))

        value = f.getvalue()
        self.assertLess(value.index("won't be"), value.index("bar.c"))
    
    def test_include_files(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.assertTrue(submit50.prompt(False, ["foo.c"], []))

        value = f.getvalue()
        self.assertLess(value.index("will be"), value.index("foo.c"))

    def test_prompt_yes(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("y")
            sys.stdin.seek(0)

            self.assertTrue(submit50.prompt(True, ["foo.c"], []))

    def test_prompt_no(self):
        f = io.StringIO()
        with self.replace_stdin(), contextlib.redirect_stdout(f):
            sys.stdin.write("n")
            sys.stdin.seek(0)

            self.assertFalse(submit50.prompt(True, ["foo.c"], []))


if __name__ == '__main__':
    unittest.main(buffer=True)
