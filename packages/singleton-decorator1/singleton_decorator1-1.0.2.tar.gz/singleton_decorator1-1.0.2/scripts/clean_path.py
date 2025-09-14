#!/usr/bin/python
"""
Usage:
eval $(clean_path.py)

Removes duplicates from PATH without changing order.
"""

from os import environ as ENV
from typing import List


def clean_path() -> None:
    """
    Gets the PATH variable from the environment, and eliminates
    duplicate entries (preserving order). If run as a command
    outputs a command to eval to re-set the path in Bash
    """
    global ENV
    new_path: List[str] = []
    if "PATH" in ENV:
        path: List[str] = ENV["PATH"].split(":")
    else:
        path = []

    for elem in path:
        if not elem in new_path:
            new_path.append(elem)

    ENV["PATH"] = ":".join(new_path)
    return


if __name__ == "__main__":
    clean_path()
    print(f"export PATH=\"{ENV['PATH']}\"")
