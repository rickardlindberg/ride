#!/usr/bin/env python3

import doctest
import importlib
import subprocess
import sys
import unittest

def ensure(command):
    process = subprocess.run(command)
    if process.returncode != 0:
        sys.exit(process.returncode)

if __name__ == "__main__":
    command = sys.argv[1:]
    if command == ["build"]:
        ensure(["ctags", "--python-kinds=-i", "-R", "."])
        suite = unittest.TestSuite()
        for module in [
            "ride",
        ]:
            suite.addTest(doctest.DocTestSuite(
                importlib.import_module(module),
                optionflags=doctest.REPORT_NDIFF|doctest.FAIL_FAST
            ))
        if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
            sys.exit(1)
    elif command[0:1] == ["commit"]:
        ensure(["bash", "-c", "if git status | grep -A 5 'Untracked files:'; then exit 1; fi"])
        ensure([sys.executable, "make.py", "build"])
        ensure(["git", "commit", "-a", "--verbose"]+command[1:])
    else:
        sys.exit("Unknown command.")
