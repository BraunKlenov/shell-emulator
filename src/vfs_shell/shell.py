"""Shell core: parses a line and dispatches it to a command."""

import getpass
import os

from .commands import COMMANDS, Result
from .parser import ParseError, parse_command_line

VFS_NAME = "vfs"
ROOT_DIR = "/"
FALLBACK_USER = "user"


def current_user():
    """Return the name of the real OS user, or a fallback."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return FALLBACK_USER


class Shell:
    """Command interpreter, independent of any user interface."""

    def __init__(self, vfs_name=VFS_NAME, env=None):
        """Create a shell for the VFS called ``vfs_name``."""
        self.vfs_name = vfs_name
        self.env = dict(os.environ if env is None else env)
        self.env.setdefault("HOME", os.path.expanduser("~"))
        self.user = current_user()
        self.cwd = ROOT_DIR

    @property
    def prompt(self):
        """Return the input prompt, e.g. ``user@vfs:/$ ``."""
        return "{}@{}:{}$ ".format(self.user, self.vfs_name, self.cwd)

    def execute(self, line):
        """Run one command line and return its ``Result``."""
        try:
            words = parse_command_line(line, self.env)
        except ParseError as error:
            message = "shell: parse error: {}".format(error)
            return Result(message, is_error=True)
        if not words:
            return Result()
        handler = COMMANDS.get(words[0])
        if handler is None:
            message = "shell: {}: command not found".format(words[0])
            return Result(message, is_error=True)
        return handler(words[1:])
