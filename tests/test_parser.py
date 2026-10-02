"""Tests for the command line parser."""

import os
import unittest
from unittest import mock

from vfs_shell.parser import ParseError, expand_variables, parse_command_line

ENV = {"HOME": "/home/student", "USER": "student", "EMPTY": ""}


class SplitTests(unittest.TestCase):
    """Word splitting, quoting and escaping."""

    def test_empty_line(self):
        """An empty or blank line gives no words."""
        self.assertEqual(parse_command_line("", ENV), [])
        self.assertEqual(parse_command_line("   \t ", ENV), [])

    def test_simple_words(self):
        """Words are separated by any amount of whitespace."""
        words = parse_command_line("ls   -l \t /tmp", ENV)
        self.assertEqual(words, ["ls", "-l", "/tmp"])

    def test_single_quotes_keep_text(self):
        """Nothing is expanded inside single quotes."""
        words = parse_command_line("echo '$HOME  a'", ENV)
        self.assertEqual(words, ["echo", "$HOME  a"])

    def test_double_quotes_expand(self):
        """Variables are expanded inside double quotes."""
        words = parse_command_line('echo "dir: $HOME"', ENV)
        self.assertEqual(words, ["echo", "dir: /home/student"])

    def test_escaped_dollar(self):
        """A backslash turns the dollar sign into plain text."""
        self.assertEqual(parse_command_line(r"echo \$HOME", ENV),
                         ["echo", "$HOME"])
        self.assertEqual(parse_command_line(r'echo "\$HOME"', ENV),
                         ["echo", "$HOME"])

    def test_empty_quotes_make_empty_word(self):
        """An empty quoted string is still an argument."""
        self.assertEqual(parse_command_line("cd ''", ENV), ["cd", ""])

    def test_unquoted_empty_expansion_vanishes(self):
        """An unquoted variable with no value gives no argument."""
        self.assertEqual(parse_command_line("cd $NOPE $EMPTY", ENV), ["cd"])

    def test_quoted_empty_expansion_is_kept(self):
        """A quoted variable with no value is an empty argument."""
        self.assertEqual(parse_command_line('cd "$NOPE"', ENV), ["cd", ""])

    def test_adjacent_parts_are_joined(self):
        """Quoted and unquoted parts glue into one word."""
        words = parse_command_line("a'b c'\"d\"e", ENV)
        self.assertEqual(words, ["ab cde"])

    def test_unterminated_single_quote(self):
        """An open single quote is an error."""
        with self.assertRaises(ParseError):
            parse_command_line("echo 'abc", ENV)

    def test_unterminated_double_quote(self):
        """An open double quote is an error."""
        with self.assertRaises(ParseError):
            parse_command_line('echo "abc', ENV)

    def test_trailing_backslash(self):
        """A backslash at the end of the line is an error."""
        with self.assertRaises(ParseError):
            parse_command_line("echo abc\\", ENV)


class ExpansionTests(unittest.TestCase):
    """Expansion of environment variables."""

    def test_dollar_name(self):
        """$NAME is replaced by the value."""
        self.assertEqual(expand_variables("$HOME/bin", ENV),
                         "/home/student/bin")

    def test_braces(self):
        """${NAME} may be glued to other text."""
        self.assertEqual(expand_variables("${USER}_1", ENV), "student_1")

    def test_undefined_is_empty(self):
        """Unknown variables expand to nothing."""
        self.assertEqual(expand_variables("a$NOPE-b", ENV), "a-b")

    def test_lone_dollar_is_literal(self):
        """A dollar sign not followed by a name stays as is."""
        self.assertEqual(expand_variables("cost: $ 5", ENV), "cost: $ 5")

    def test_bad_substitution(self):
        """An invalid name inside braces is an error."""
        with self.assertRaises(ParseError):
            expand_variables("${a b}", ENV)
        with self.assertRaises(ParseError):
            expand_variables("${}", ENV)

    def test_unterminated_brace(self):
        """A missing closing brace is an error."""
        with self.assertRaises(ParseError):
            expand_variables("${HOME", ENV)

    def test_real_environment_by_default(self):
        """Without an explicit mapping the real environment is used."""
        with mock.patch.dict(os.environ, {"VFS_TEST_VAR": "42"}):
            self.assertEqual(parse_command_line("echo $VFS_TEST_VAR"),
                             ["echo", "42"])


if __name__ == "__main__":
    unittest.main()
