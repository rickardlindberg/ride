#!/usr/bin/env python3

import doctest
import importlib
import subprocess
import sys
import unittest

def main():
    command = sys.argv[1:]
    if command == ["build"]:
        ensure(["ctags", "--python-kinds=-i", "-R", "."])
        run_tests()
    elif command[0:1] == ["commit"]:
        ensure(["bash", "-c", "if git status | grep -A 5 'Untracked files:'; then exit 1; fi"])
        ensure([sys.executable, "make.py", "build"])
        ensure(["git", "commit", "--verbose"]+command[1:])
    elif command[0:1] == ["integrate"]:
        ensure(
            ["bash", "-c", 'test "$(git status --porcelain)" = ""'],
            "git status is not empty"
        )
        run_tests()
        ensure(["git", "push"])
    elif command[0:1] == ["rundev"]:
        ensure([sys.executable, "ride.py"]+command[1:])
    else:
        sys.exit("Unknown command.")

def ensure(command, message=None):
    process = subprocess.run(command)
    if process.returncode != 0:
        if message:
            print(f"ERROR: {message}")
        sys.exit(process.returncode)

def run_tests():
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

if __name__ == "__main__":
    main()
