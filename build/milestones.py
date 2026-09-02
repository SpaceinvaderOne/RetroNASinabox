"""Deciding what a build's console output actually proves.

The gate for publishing. Success is asserted only on positive evidence: a log
with neither marker is INCOMPLETE, never SUCCEEDED, because a build that timed
out has told us nothing about whether it worked.
"""

from enum import StrEnum

from build.payload import MARKER_FAIL, MARKER_OK


class Outcome(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


def read_console(text: str) -> Outcome:
    """Failure outranks success: if the guest ever reported a failure, the
    image is not publishable regardless of what it said afterwards."""
    if MARKER_FAIL in text:
        return Outcome.FAILED
    if MARKER_OK in text:
        return Outcome.SUCCEEDED
    return Outcome.INCOMPLETE


def tail(text: str, lines: int = 20) -> str:
    """Last `lines` lines, guarding the `-0 == 0` trap: a naive `[-lines:]`
    slice returns the *entire* text when `lines` is 0, not nothing."""
    if lines <= 0:
        return ""
    return "\n".join(text.splitlines()[-lines:])


LOGIN_PROMPT = "login:"
PANIC = "Kernel panic"
EMERGENCY = "Emergency Mode"


def booted_ok(text: str) -> bool:
    """Did a finished image actually come up on its own?

    Positive evidence only: a getty login prompt means userspace reached the
    point of accepting logins. The absence of a panic proves nothing on its
    own, so it is never sufficient here -- but a panic or a drop to emergency
    mode overrides a prompt that appeared before things fell over.
    """
    if PANIC in text or EMERGENCY in text:
        return False
    return LOGIN_PROMPT in text
