"""Command line parsing: word splitting and variable expansion."""

import os
import re

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = "\\"
DOUBLE_ESCAPABLE = '"\\$'
NOT_FOUND = -1
PLAIN_CHUNK = re.compile(r"[^\s'\"\\]+")
VARIABLE = re.compile(r"\$(?:(\w+)|\{([^}]*)(\}?))")
NAME = re.compile(r"\w+")


class ParseError(ValueError):
    """Raised when a command line cannot be parsed."""


def _substitute(match, env):
    """Return the replacement text for one variable reference."""
    name = match.group(1)
    if name:
        return env.get(name, "")
    name, closing = match.group(2), match.group(3)
    if not closing:
        raise ParseError("unterminated '${' expansion")
    if not NAME.fullmatch(name):
        raise ParseError("bad substitution: ${%s}" % name)
    return env.get(name, "")


def expand_variables(text, env=None):
    """Replace ``$NAME`` and ``${NAME}`` with values from ``env``.

    By default the environment of the real OS (``os.environ``) is used.
    Undefined variables expand to an empty string, as in POSIX shells.
    """
    source = os.environ if env is None else env
    return VARIABLE.sub(lambda match: _substitute(match, source), text)


class _Scanner:
    """Splits a command line into words honouring quotes and escapes."""

    def __init__(self, line, env):
        """Prepare scanning of ``line`` using variables from ``env``."""
        self.line = line
        self.env = env
        self.pos = 0
        self.words = []
        self.parts = []
        self.in_word = False

    def scan(self):
        """Return the list of words found in the line."""
        while self.pos < len(self.line):
            self._step(self.line[self.pos])
        self._finish_word()
        return self.words

    def _step(self, char):
        """Consume the next piece of input starting with ``char``."""
        if char.isspace():
            self._finish_word()
            self.pos += 1
        elif char == SINGLE_QUOTE:
            self._read_single()
        elif char == DOUBLE_QUOTE:
            self._read_double()
        elif char == BACKSLASH:
            self._read_escape()
        else:
            self._read_plain()

    def _finish_word(self):
        """Complete the current word, if any, and start a new one."""
        if self.in_word:
            self.words.append("".join(self.parts))
        self.parts = []
        self.in_word = False

    def _add_literal(self, text):
        """Append text to the current word without expansion."""
        self.parts.append(text)
        self.in_word = True

    def _add_expanded(self, text):
        """Append text to the current word expanding variables."""
        self._add_literal(expand_variables(text, self.env))

    def _read_plain(self):
        """Read an unquoted run of characters."""
        match = PLAIN_CHUNK.match(self.line, self.pos)
        value = expand_variables(match.group(), self.env)
        if value:
            self._add_literal(value)
        self.pos = match.end()

    def _read_single(self):
        """Read a single-quoted string: nothing is expanded inside."""
        start = self.pos + 1
        end = self.line.find(SINGLE_QUOTE, start)
        if end == NOT_FOUND:
            raise ParseError("unterminated single quote")
        self._add_literal(self.line[start:end])
        self.pos = end + 1

    def _next_is_escapable(self):
        """Tell whether a backslash here escapes the next character."""
        return (self.pos < len(self.line)
                and self.line[self.pos] in DOUBLE_ESCAPABLE)

    def _read_double(self):
        """Read a double-quoted string: variables are expanded."""
        self.pos += 1
        pending = []
        while self.pos < len(self.line):
            char = self.line[self.pos]
            self.pos += 1
            if char == DOUBLE_QUOTE:
                self._add_expanded("".join(pending))
                return
            if char == BACKSLASH and self._next_is_escapable():
                self._add_expanded("".join(pending))
                pending = []
                self._add_literal(self.line[self.pos])
                self.pos += 1
            else:
                pending.append(char)
        raise ParseError("unterminated double quote")

    def _read_escape(self):
        """Read a backslash followed by a literal character."""
        self.pos += 1
        if self.pos >= len(self.line):
            raise ParseError("trailing backslash")
        self._add_literal(self.line[self.pos])
        self.pos += 1


def parse_command_line(line, env=None):
    """Split ``line`` into words and expand environment variables.

    Supports single quotes (no expansion), double quotes (with
    expansion) and backslash escapes. Raises ``ParseError`` for
    malformed input such as an unterminated quote.
    """
    source = os.environ if env is None else env
    return _Scanner(line, source).scan()
