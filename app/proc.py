"""Run an external command and capture what it said."""

import subprocess

DEFAULT_TIMEOUT = 60.0

# Conventional "timed out" exit status, as GNU coreutils' `timeout` uses.
TIMEOUT_EXIT_CODE = 124

# Conventional "command not found" exit status, as a shell uses.
NOT_EXECUTABLE_EXIT_CODE = 127


def run(argv: list[str], timeout: float = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    """Return (exit code, stdout, stderr). Never raises on a non-zero exit —
    callers decide which failures matter.
    """
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired as expired:
        # Not an OSError -- subprocess.run raises this itself on a deadline it
        # enforces, independently of the OSError clause below.
        #
        # TimeoutExpired carries whatever was captured before the deadline --
        # and carries it as bytes even under text=True. Returning "" would
        # throw away the only evidence of what the command was doing, which
        # matters most for commands that are EXPECTED to hit their deadline.
        partial = expired.stdout or b""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        return (
            TIMEOUT_EXIT_CODE,
            partial,
            f"{argv[0] if argv else 'command'} timed out after {timeout:g}s and was "
            "killed. The server may be busy, or libvirt or a disk may not be "
            "responding.",
        )
    except OSError as exc:
        # The OS itself refused to run the binary -- missing, not executable,
        # or similar (FileNotFoundError, PermissionError, ...). Report only
        # what was observed: the command could not be run, and why the OS
        # said so.
        return (
            NOT_EXECUTABLE_EXIT_CODE,
            "",
            f"{argv[0] if argv else 'command'} could not be run: {exc}",
        )
    return completed.returncode, completed.stdout, completed.stderr
