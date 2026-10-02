"""Tkinter graphical front-end of the shell emulator."""

import tkinter as tk

from .shell import Shell

TITLE_TEMPLATE = "Shell emulator - VFS: {}"
WINDOW_SIZE = "820x520"
FONT = ("Courier", 12)
BACKGROUND = "#1e1e1e"
FOREGROUND = "#d4d4d4"
PROMPT_COLOR = "#6a9955"
ERROR_COLOR = "#f48771"
BANNER = "Shell emulator (stage 1: REPL). Commands: ls, cd, exit.\n"
INPUT_START = "input_start"
END_OF_INPUT = "end-1c"
BREAK = "break"
EMPTY_HISTORY = ""


class ShellWindow:
    """Terminal-like window: a text area with an editable last line."""

    def __init__(self, root, shell):
        """Build the window inside ``root`` for the given ``shell``."""
        self.root = root
        self.shell = shell
        self.history = []
        self.history_pos = 0
        self.exit_code = 0
        root.title(TITLE_TEMPLATE.format(shell.vfs_name))
        root.geometry(WINDOW_SIZE)
        self.text = self._create_text()
        self._bind_events()
        self._print(BANNER)
        self._show_prompt()

    def _create_text(self):
        """Create the scrollable text widget and its colour tags."""
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text = tk.Text(frame, font=FONT, bg=BACKGROUND, fg=FOREGROUND,
                       insertbackground=FOREGROUND, wrap=tk.WORD,
                       yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        text.tag_config("prompt", foreground=PROMPT_COLOR)
        text.tag_config("error", foreground=ERROR_COLOR)
        text.focus_set()
        return text

    def _bind_events(self):
        """Attach keyboard handlers to the text widget."""
        self.text.bind("<Return>", self._on_return)
        self.text.bind("<BackSpace>", self._on_backspace)
        self.text.bind("<Left>", self._on_backspace)
        self.text.bind("<Delete>", self._on_delete)
        self.text.bind("<Home>", self._on_home)
        self.text.bind("<Up>", self._on_up)
        self.text.bind("<Down>", self._on_down)
        self.text.bind("<Key>", self._on_key)

    def _print(self, text, tag=None):
        """Append ``text`` to the end of the output area."""
        self.text.insert(tk.END, text, tag)
        self.text.see(tk.END)

    def _show_prompt(self):
        """Print the prompt and open a new input line after it."""
        self._print(self.shell.prompt, "prompt")
        self.text.mark_set(INPUT_START, END_OF_INPUT)
        self.text.mark_gravity(INPUT_START, tk.LEFT)
        self.history_pos = len(self.history)

    def _show_result(self, result):
        """Print the output of a command, errors in a separate colour."""
        if result.output:
            tag = "error" if result.is_error else None
            self._print(result.output + "\n", tag)

    def _replace_input(self, new_text):
        """Replace the text of the current input line."""
        self.text.delete(INPUT_START, END_OF_INPUT)
        self.text.insert(END_OF_INPUT, new_text)

    def _before_input(self, operator):
        """Compare the cursor position with the start of input."""
        return self.text.compare(tk.INSERT, operator, INPUT_START)

    def _on_return(self, _event):
        """Execute the line typed by the user."""
        line = self.text.get(INPUT_START, END_OF_INPUT)
        self._print("\n")
        if line.strip():
            self.history.append(line)
        result = self.shell.execute(line)
        self._show_result(result)
        if result.exit_requested:
            self.exit_code = result.exit_code
            self.root.destroy()
        else:
            self._show_prompt()
        return BREAK

    def _on_backspace(self, _event):
        """Forbid deleting or moving into the read-only prompt."""
        if self._before_input("<="):
            return BREAK
        return None

    def _on_delete(self, _event):
        """Forbid deleting text inside the read-only area."""
        if self._before_input("<"):
            return BREAK
        return None

    def _on_home(self, _event):
        """Move the cursor to the start of the input, after the prompt."""
        self.text.mark_set(tk.INSERT, INPUT_START)
        return BREAK

    def _on_key(self, event):
        """Jump to the input line when typing into the read-only area."""
        typed = bool(event.char) and event.char.isprintable()
        if typed and self._before_input("<"):
            self.text.mark_set(tk.INSERT, END_OF_INPUT)
        return None

    def _on_up(self, _event):
        """Show the previous command from the history."""
        if self.history_pos:
            self.history_pos -= 1
            self._replace_input(self.history[self.history_pos])
        return BREAK

    def _on_down(self, _event):
        """Show the next command from the history."""
        if self.history_pos < len(self.history):
            self.history_pos += 1
            self._replace_input(self._history_entry())
        return BREAK

    def _history_entry(self):
        """Return the history item at the current position, or empty."""
        if self.history_pos < len(self.history):
            return self.history[self.history_pos]
        return EMPTY_HISTORY


def run_gui(shell=None):
    """Open the window, run the event loop and return the exit code."""
    root = tk.Tk()
    window = ShellWindow(root, shell or Shell())
    root.mainloop()
    return window.exit_code
