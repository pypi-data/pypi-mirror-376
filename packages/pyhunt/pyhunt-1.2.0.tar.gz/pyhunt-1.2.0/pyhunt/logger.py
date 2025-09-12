from typing import Any, Dict, Optional
import threading
import atexit
from pathlib import Path
from datetime import datetime
from pyhunt.console import Console
from pyhunt.config import (
    LOG_LEVEL,
    LOG_LEVELS,
    MAX_REPEAT,
    ELAPSED,
    LOG_FILE,
    COLOR_ENABLED,
)
from pyhunt.colors import build_indent, get_color
from pyhunt.context import call_depth
from pyhunt.helpers import pretty_json


class FileLogger:
    def __init__(self, filename: str = None):
        self.filename = filename
        self.file_path = Path(self.filename) if filename else None
        self.enabled = bool(filename)  # Only enabled if filename is provided
        self.session_lines = []
        self.session_started = False

    def _get_session_header(self) -> str:
        """
        Get formatted session header with date and time.
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S.%f")[:-3]  # Format: 14:30:45.123
        return f"=== {date_str} {time_str} ==="

    def start_session(self):
        """
        Start a new logging session.
        """
        if not self.session_started:
            self.session_lines = []
            self.session_started = True

    def end_session(self):
        """
        End the current logging session and write all output as one block.
        """
        if self.session_started and self.session_lines:
            try:
                # Read existing content
                existing_content = ""
                if self.file_path.exists():
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()

                # Write new content at the beginning with session header
                with open(self.file_path, "w", encoding="utf-8") as f:
                    # Add session header
                    f.write(f"{self._get_session_header()}\n")
                    # Add all session lines
                    for line in self.session_lines:
                        f.write(f"{line}\n")
                    # Add separator
                    f.write("\n")
                    # Add existing content
                    if existing_content:
                        f.write(existing_content)

                # Reset session
                self.session_lines = []
                self.session_started = False
            except Exception:
                # Silently fail if file logging fails
                pass

    def write(self, message: str):
        """
        Add message lines to the current session.
        """
        if not self.enabled:
            return

        # Split message into lines and add to session
        lines = message.split("\n")
        for line in lines:
            self.session_lines.append(line)

    def write_raw(self, message: str):
        """
        Add raw message to the current session.
        """
        if not self.enabled:
            return

        # Add message to session lines
        lines = message.split("\n")
        for line in lines:
            self.session_lines.append(line)

    def print_with_file_logging(self, message: str, console, end="\n"):
        """
        Print message to console and also write to file (with markup stripped).
        """
        console.print(message, end=end)
        clean_message = _strip_markup(message)

        # Add message to the current session
        if self.session_started:
            # Split clean message into lines and add to session
            lines = clean_message.split("\n")
            for line in lines:
                self.session_lines.append(line)


# Initialize file logger
# Initialize file logger only if LOG_FILE is set
file_logger = FileLogger(LOG_FILE) if LOG_FILE else None

# Start session when module is imported if file logger exists
if file_logger:
    file_logger.start_session()
    # Register cleanup function to end session on exit
    atexit.register(file_logger.end_session)
else:
    # Create a dummy file logger for type consistency
    file_logger = FileLogger(None)

# Initialize Rich Console
console = Console()


# Helper function to get emoji or text replacement based on color setting
def _get_emoji_or_text(color_emoji: str, text_replacement: str) -> str:
    """Return emoji if color is enabled, otherwise return text replacement."""
    return color_emoji if COLOR_ENABLED else text_replacement


# --- Log suppression mechanism ---
_log_count_map = {}
_log_count_lock = threading.Lock()


def _strip_markup(text: str) -> str:
    """
    Remove all markup tags from text for clean file output.
    """
    import re as re_module

    # Remove all markup tags [something]content[/]
    text = re_module.sub(r"\[[^\]]+\]", "", text)
    # Remove closing tags [/] or [/something]
    text = re_module.sub(r"\[/[^\]]*\]", "", text)
    return text


def _write_to_file(message: str) -> None:
    """
    Write message to log file with markup stripped.
    """
    clean_message = _strip_markup(message)
    file_logger.write(clean_message)


def _should_suppress_log(key):
    """Returns True if the log for this key should be suppressed, False otherwise.
    If suppression is triggered, returns a tuple (suppress, show_ellipsis) where:
      - suppress: True if log should be suppressed
      - show_ellipsis: True if "... 생략 ..." should be shown (only once per key)
    """
    if MAX_REPEAT is None or MAX_REPEAT < 1:
        return False, False
    with _log_count_lock:
        count = _log_count_map.get(key, 0)
        if count < MAX_REPEAT:
            _log_count_map[key] = count + 1
            return False, False
        elif count == MAX_REPEAT:
            _log_count_map[key] = count + 1
            return True, True  # Suppress log, but show ellipsis
        else:
            return True, False  # Suppress log, no ellipsis


# --- End log suppression mechanism ---


def _format_truncation_message(event_type, depth):
    color = "#808080"
    msg = f"[{color}] ... Repeated logs have been omitted | MAX_REPEAT: {MAX_REPEAT}[/]"
    return format_with_tree_indent(msg, depth, event_type)


def should_log(level_name: str) -> bool:
    """
    Determine if a message at the given level should be logged.
    """
    level_value = LOG_LEVELS.get(level_name.lower(), 20)
    return level_value >= LOG_LEVEL


def format_with_tree_indent(message: str, depth: int, event_type: str) -> str:
    """
    Apply tree indentation and prefix symbols to a multi-line log message.

    Args:
        message: The pure log message without indentation.
        depth: The call depth for indentation.
        event_type: One of 'entry', 'exit', 'error'.

    Returns:
        The message decorated with tree indentation and symbols.
    """

    color = get_color(depth)
    indent = build_indent(depth)

    # Determine prefix symbols based on event type
    if event_type == "entry":
        first_prefix = f"{indent}[{color}]├─▶[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    elif event_type == "exit":
        first_prefix = f"{indent}[{color}]├──[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    elif event_type == "error":
        first_prefix = f"{indent}[{color}]└──[/] "
        child_prefix = f"{indent}[{color}]│    [/] "
    else:
        first_prefix = f"{indent}[{color}]│   [/] "
        child_prefix = f"{indent}[{color}]│   [/] "

    # Apply child prefix to log messages, filtering empty lines
    lines = message.splitlines()
    if not lines:
        return ""

    decorated_lines = [f"{first_prefix}{lines[0]}"]
    decorated_lines += [f"{child_prefix}{line}" for line in lines[1:]]
    return "\n".join(decorated_lines)


def log_entry(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    call_args: Dict[str, Any],
    location: str,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[bold {color}]{name}[/]"
    colored_location = f"[bold {color}]{location}[/]"

    # Suppression key: (event_type, func_name, class_name, location)
    suppress_key = ("entry", func_name, class_name, location)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("entry", depth)
            try:
                if should_log("debug"):
                    file_logger.print_with_file_logging(trunc_msg, console)
            except Exception:
                pass
        return

    args_to_format = {k: v for k, v in call_args.items() if k != "self"}
    if not args_to_format:
        args_json_str = ""
    else:
        args_json_str = pretty_json(args_to_format, "", "", color)

    entry_indicator = _get_emoji_or_text("🟢", "→")
    core_parts = [
        f"{depth_str} {entry_indicator} Entry {sync_async}{colored_name} | {colored_location}",
        args_json_str,
    ]
    core_message = "\n".join(m for m in core_parts if m and m.strip())
    message = format_with_tree_indent(core_message, depth, "entry")

    try:
        if should_log("debug"):
            file_logger.print_with_file_logging(message, console)
    except Exception as e:
        file_logger.print_with_file_logging(
            f"[bold red]Error during logging for {name}: {e}[/]", console
        )


def log_exit(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    elapsed: float,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[{color}]{name}[/]"

    # Suppression key: (event_type, func_name, class_name)
    suppress_key = ("exit", func_name, class_name)
    suppress, _ = _should_suppress_log(suppress_key)
    if suppress:
        return

    elapsed_str = f" | {elapsed:.4f}s" if ELAPSED else ""
    exit_indicator = _get_emoji_or_text("🔳", "←")
    core_message = (
        f"{depth_str} {exit_indicator} Exit {sync_async}{colored_name}{elapsed_str}"
    )
    message = format_with_tree_indent(core_message, depth, "exit")

    try:
        if should_log("debug"):
            file_logger.print_with_file_logging(message, console)
    except Exception as e:
        file_logger.print_with_file_logging(
            f"[bold red]Error during logging for {name}: {e}[/]", console
        )


def log_error(
    func_name: str,
    class_name: Optional[str],
    is_async: bool,
    elapsed: float,
    exception: Exception,
    call_args: Dict[str, Any],
    location: str,
    depth: int,
) -> None:
    color = get_color(depth)

    sync_async = "async " if is_async else ""
    name = f"{class_name}.{func_name}" if class_name else func_name
    depth_str = f"[{color}]{depth}[/]"
    colored_name = f"[bold {color}]{name}[/]"
    colored_location = f"[bold {color}]{location}[/]"

    # Suppression key: (event_type, func_name, class_name, precise_location)
    suppress_key = ("error", func_name, class_name, location)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("error", depth)
            try:
                if should_log("debug"):
                    file_logger.print_with_file_logging(trunc_msg, console)
            except Exception:
                pass
        return

    args_to_format = {k: v for k, v in call_args.items() if k != "self"}
    if not args_to_format:
        args_json_str = ""
    else:
        args_json_str = pretty_json(args_to_format, "", "", color)

    error_indicator = _get_emoji_or_text("🟥", "!")
    core_parts = [
        f"{depth_str} {error_indicator} Error {sync_async} {colored_name} | {colored_location}{f' | {elapsed:.4f}s' if ELAPSED else ''}",
        f"[bold #E32636]{type(exception).__name__}: {exception}[/]",
        args_json_str,
    ]
    core_message = "\n".join(m for m in core_parts if m and m.strip())
    message = format_with_tree_indent(core_message, depth, "error")

    try:
        if should_log("debug"):
            file_logger.print_with_file_logging(message, console)
    except Exception as e:
        file_logger.print_with_file_logging(
            f"[bold red]Error during error logging for {name}: {e}[/]", console
        )


def styled_log(level_name: str, message: str, depth: int = 0) -> None:
    color = get_color(depth)
    depth_str = f" [{color}]{depth}[/]"

    # Suppression key: (level_name, message)
    suppress_key = ("styled", level_name, message)
    suppress, show_trunc = _should_suppress_log(suppress_key)
    if suppress:
        if show_trunc:
            trunc_msg = _format_truncation_message("", depth)
            if should_log(level_name):
                file_logger.print_with_file_logging(trunc_msg, console)
        return

    if level_name.lower() in ("debug", "info"):
        label = f"[cyan]{level_name.upper()}[/cyan]"
    elif level_name.lower() == "warning":
        label = f"[yellow]{level_name.upper()}[/yellow]"
    elif level_name.lower() in ("error", "critical"):
        label = f"[bold red]{level_name.upper()}[/bold red]"
    else:
        label = level_name.upper()

    core_message = f"{depth_str} {label} {message}"
    formatted_message = format_with_tree_indent(core_message, depth, "")
    if should_log(level_name):
        file_logger.print_with_file_logging(formatted_message, console)
        # _write_to_file(formatted_message)  # Already handled by print_with_file_logging


def debug(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("debug", message, current_depth)


def info(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("info", message, current_depth)


def warning(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("warning", message, current_depth)


def critical(message: str, *args, **kwargs) -> None:
    current_depth = 0
    try:
        current_depth = call_depth.get()
    except LookupError:
        pass
    styled_log("critical", message, current_depth)
