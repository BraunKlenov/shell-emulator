"""Tests for the graphical window (skipped without a display)."""

import unittest

try:
    import tkinter as tk
except ImportError:
    tk = None

from vfs_shell.shell import Shell


def make_window():
    """Create a hidden root and a window, or return None if impossible."""
    if tk is None:
        return None
    from vfs_shell.gui import ShellWindow
    try:
        root = tk.Tk()
    except tk.TclError:
        return None
    root.withdraw()
    return ShellWindow(root, Shell("guivfs", {"HOME": "/h"}))


class GuiTests(unittest.TestCase):
    """Behaviour of ``ShellWindow``."""

    def setUp(self):
        """Create the window or skip the test."""
        self.window = make_window()
        if self.window is None:
            self.skipTest("tkinter or display is not available")

    def tearDown(self):
        """Destroy the window."""
        try:
            self.window.root.destroy()
        except tk.TclError:
            pass

    def type_line(self, line):
        """Type a line into the input area and press Enter."""
        self.window.text.insert("end-1c", line)
        self.window._on_return(None)

    def content(self):
        """Return all text shown in the window."""
        return self.window.text.get("1.0", "end-1c")

    def test_title_contains_vfs_name(self):
        """The window title shows the VFS name."""
        self.assertIn("guivfs", self.window.root.title())

    def test_command_output_is_shown(self):
        """Output of a command appears in the window."""
        self.type_line("ls -a")
        self.assertIn("command: ls, arguments: ['-a']", self.content())

    def test_variable_is_expanded(self):
        """Variables are expanded before the command runs."""
        self.type_line("cd $HOME")
        self.assertIn("arguments: ['/h']", self.content())

    def test_error_is_shown(self):
        """Errors are displayed in the window."""
        self.type_line("nope")
        self.assertIn("command not found", self.content())

    def test_exit_closes_window(self):
        """The exit command closes the window and keeps the code."""
        self.type_line("exit 5")
        self.assertEqual(self.window.exit_code, 5)


if __name__ == "__main__":
    unittest.main()
