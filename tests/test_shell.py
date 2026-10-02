"""Tests for the shell core and the built-in commands."""

import unittest

from vfs_shell.shell import Shell

ENV = {"HOME": "/home/student"}


class ShellTests(unittest.TestCase):
    """Behaviour of ``Shell.execute``."""

    def setUp(self):
        """Create a fresh shell with a fixed environment."""
        self.shell = Shell("testvfs", ENV)

    def test_prompt_contains_vfs_name(self):
        """The prompt shows the VFS name."""
        self.assertIn("@testvfs:", self.shell.prompt)

    def test_empty_line_does_nothing(self):
        """A blank line produces no output and no error."""
        result = self.shell.execute("   ")
        self.assertEqual(result.output, "")
        self.assertFalse(result.is_error)
        self.assertFalse(result.exit_requested)

    def test_ls_stub(self):
        """The ls stub prints its name and arguments."""
        result = self.shell.execute("ls -l /tmp")
        self.assertEqual(
            result.output, "command: ls, arguments: ['-l', '/tmp']")
        self.assertFalse(result.is_error)

    def test_cd_stub_expands_variables(self):
        """Arguments of the cd stub have variables expanded."""
        result = self.shell.execute("cd $HOME")
        self.assertEqual(
            result.output, "command: cd, arguments: ['/home/student']")

    def test_stub_without_arguments(self):
        """A stub called without arguments prints an empty list."""
        result = self.shell.execute("ls")
        self.assertEqual(result.output, "command: ls, arguments: []")

    def test_home_is_defined_if_missing(self):
        """HOME gets a default value when the OS does not set it."""
        shell = Shell("v", {})
        self.assertTrue(shell.env["HOME"])

    def test_unknown_command(self):
        """An unknown command is reported as an error."""
        result = self.shell.execute("foo bar")
        self.assertTrue(result.is_error)
        self.assertEqual(result.output, "shell: foo: command not found")

    def test_parse_error_is_reported(self):
        """A parsing problem becomes an error result."""
        result = self.shell.execute("ls 'oops")
        self.assertTrue(result.is_error)
        self.assertIn("parse error", result.output)


class ExitTests(unittest.TestCase):
    """Behaviour of the exit command."""

    def setUp(self):
        """Create a fresh shell with a fixed environment."""
        self.shell = Shell("testvfs", ENV)

    def test_exit_default_code(self):
        """Plain exit terminates with code zero."""
        result = self.shell.execute("exit")
        self.assertTrue(result.exit_requested)
        self.assertEqual(result.exit_code, 0)

    def test_exit_with_code(self):
        """Exit accepts a numeric code."""
        result = self.shell.execute("exit 3")
        self.assertTrue(result.exit_requested)
        self.assertEqual(result.exit_code, 3)

    def test_exit_code_wraps_like_posix(self):
        """Exit codes are taken modulo 256."""
        self.assertEqual(self.shell.execute("exit 256").exit_code, 0)
        self.assertEqual(self.shell.execute("exit -1").exit_code, 255)

    def test_exit_non_numeric(self):
        """A non-numeric code is an error and the shell stays alive."""
        result = self.shell.execute("exit abc")
        self.assertTrue(result.is_error)
        self.assertFalse(result.exit_requested)

    def test_exit_too_many_arguments(self):
        """Extra arguments are an error and the shell stays alive."""
        result = self.shell.execute("exit 1 2")
        self.assertTrue(result.is_error)
        self.assertFalse(result.exit_requested)


if __name__ == "__main__":
    unittest.main()
