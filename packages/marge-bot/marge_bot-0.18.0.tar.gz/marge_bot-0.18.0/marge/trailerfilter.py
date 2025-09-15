#!/usr/bin/env python3
"""Executable script to pass to git filter-branch --msgfilter to rewrite trailers.

This treats everything (stdin, stdout, env) at the level of raw bytes which are
assumed to be utf-8, or more specifically some ASCII superset, regardless of
(possibly broken) LOCALE settings.

"""
import collections
import os
import re
import sys
from typing import NoReturn

STDIN = sys.stdin.buffer
STDOUT = sys.stdout.buffer
STDERR = sys.stderr.buffer


def die(msg: bytes) -> NoReturn:
    STDERR.write(b"ERROR: ")
    STDERR.write(msg)
    sys.exit(1)


def drop_trailing_newlines(lines: list[bytes]) -> None:
    while lines and not lines[-1]:
        del lines[-1]


def remove_duplicates(trailers: list[bytes]) -> list[bytes]:
    return list(collections.OrderedDict((t, None) for t in trailers).keys())


def rework_commit_message(
    commit_message: bytes, trailers: list[bytes], keep_trailers: bool
) -> bytes:
    if not commit_message:
        die(b"Expected a non-empty commit message")

    trailer_names = [trailer.split(b":", 1)[0].lower() for trailer in trailers]

    filtered_lines = [
        line.rstrip()
        for line in commit_message.split(b"\n")
        if keep_trailers or line.split(b":", 1)[0].lower() not in trailer_names
    ]

    reworked_lines = filtered_lines[:]

    drop_trailing_newlines(reworked_lines)
    while len(reworked_lines) > 1 and re.match(rb"^[A-Z][\w-]+: ", reworked_lines[-1]):
        trailers.insert(0, reworked_lines.pop())
    if not reworked_lines:
        die(b"Your commit message seems to consist only of Trailers: " + commit_message)

    drop_trailing_newlines(reworked_lines)

    non_empty_trailers = remove_duplicates(
        [t for t in trailers if t.split(b": ", 1)[1].strip()]
    )
    if non_empty_trailers:
        reworked_lines += [b""] + non_empty_trailers
    reworked_lines += [b""]
    return b"\n".join(reworked_lines)


def main() -> int:
    trailers = os.environb[b"TRAILERS"].split(b"\n") if os.environb[b"TRAILERS"] else []
    keep_trailers: bool = os.environb.get(b"KEEP_TRAILERS", b"False") == b"True"
    assert all(b":" in trailer for trailer in trailers), trailers
    original_commit_message = STDIN.read().strip()
    new_commit_message = rework_commit_message(
        original_commit_message, trailers, keep_trailers
    )
    STDOUT.write(new_commit_message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
