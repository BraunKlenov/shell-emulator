"""Built-in commands of the emulator."""

from dataclasses import dataclass
from typing import Optional

MAX_EXIT_ARGS = 1
DEFAULT_EXIT_CODE = 0
EXIT_CODE_MODULO = 256


@dataclass
class Result:
    """Outcome of executing one command line."""

    output: str = ""
    is_error: bool = False
    exit_code: Optional[int] = None

    @property
    def exit_requested(self):
        """Tell whether the shell must terminate."""
        return self.exit_code is not None


def describe_call(name, args):
    """Format the output of a stub command: its name and arguments."""
    return "command: {}, arguments: {}".format(name, args)


def cmd_ls(args):
    """Stub of ``ls``: print own name and arguments."""
    return Result(describe_call("ls", args))


def cmd_cd(args):
    """Stub of ``cd``: print own name and arguments."""
    return Result(describe_call("cd", args))


def cmd_exit(args):
    """Terminate the shell with an optional numeric exit code."""
    if len(args) > MAX_EXIT_ARGS:
        return Result("exit: too many arguments", is_error=True)
    if not args:
        return Result(exit_code=DEFAULT_EXIT_CODE)
    try:
        code = int(args[0])
    except ValueError:
        message = "exit: {}: numeric argument required".format(args[0])
        return Result(message, is_error=True)
    return Result(exit_code=code % EXIT_CODE_MODULO)


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
}
