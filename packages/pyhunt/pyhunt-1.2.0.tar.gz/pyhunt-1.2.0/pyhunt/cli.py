import argparse
import sys
from dotenv import load_dotenv
from pathlib import Path

from pyhunt.config import LOG_LEVELS
from pyhunt.console import Console

console = Console()
env_path = Path.cwd() / ".env"


def load_env() -> dict:
    """Load existing .env into dict."""
    load_dotenv(env_path, override=True)
    env_vars = {}
    if env_path.exists():
        with env_path.open("r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value
    return env_vars


def save_env(env_vars: dict):
    """Write dict back into .env file with preferred order."""
    order = ["ROOT_DIR", "HUNT_LEVEL", "HUNT_MAX_REPEAT", "HUNT_COLOR", "HUNT_LOG_FILE"]
    with env_path.open("w") as f:
        for key in order:
            if key in env_vars:
                f.write(f"{key}={env_vars.pop(key)}\n")
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")


def update_env_vars(new_vars: dict):
    """Update or create .env file with provided vars."""
    env_vars = load_env()
    env_vars.update({k: str(v) for k, v in new_vars.items()})
    save_env(env_vars)


def print_log_level_message(level_name: str):
    """Print visible log levels for given level."""
    level_name = level_name.lower()
    level_value = LOG_LEVELS.get(level_name, 20)
    visible_levels = [n.upper() for n, v in LOG_LEVELS.items() if v >= level_value]

    colors = {
        "debug": "cyan",
        "info": "green",
        "warning": "yellow",
        "error": "red",
        "critical": "bold red",
    }
    colored_level = f"[{colors.get(level_name, 'white')}]{level_name.upper()}[/]"
    colored_visible = [
        f"[{colors.get(level.lower(), 'white')}]{level}[/]" for level in visible_levels
    ]

    console.print(
        f"HUNT_LEVEL set to '{colored_level}'. "
        f"You will see logs with levels: {', '.join(colored_visible)}."
    )


def main():
    parser = argparse.ArgumentParser(prog="hunt", description="Pythunt CLI tool")

    group = parser.add_mutually_exclusive_group()
    for lvl in ["debug", "info", "warning", "error", "critical"]:
        group.add_argument(
            f"--{lvl}", action="store_true", help=f"Set log level to {lvl.upper()}"
        )

    parser.add_argument(
        "--root", action="store_true", help="Set ROOT_DIR to current directory"
    )
    parser.add_argument("--repeat", type=int, help="Set HUNT_MAX_REPEAT")
    parser.add_argument(
        "--color", choices=["true", "false"], help="Enable/disable color output"
    )
    parser.add_argument(
        "--log-file",
        nargs="?",
        const=".pyhunt.log",
        help="Set log file (default: .pyhunt.log)",
    )

    # If `--` is present, parse only args after separator
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    )

    updates = {}

    # Defaults when no args
    if not sys.argv[1:]:
        updates["HUNT_LEVEL"] = "DEBUG"
        updates["ROOT_DIR"] = str(Path.cwd())
        print_log_level_message("debug")
        console.print(f"ROOT_DIR set to '{updates['ROOT_DIR']}'")
    else:
        # Log level
        for lvl in ["debug", "info", "warning", "error", "critical"]:
            if getattr(args, lvl):
                updates["HUNT_LEVEL"] = lvl.upper()
                print_log_level_message(lvl)
                break

        if args.root:
            updates["ROOT_DIR"] = str(Path.cwd())
            console.print(f"ROOT_DIR set to '{updates['ROOT_DIR']}'")

        if args.repeat is not None:
            updates["HUNT_MAX_REPEAT"] = args.repeat
            console.print(f"HUNT_MAX_REPEAT set to '{args.repeat}'")

        if args.color:
            updates["HUNT_COLOR"] = args.color
            console.print(f"Color output set to '{args.color}'")

        if args.log_file is not None:
            # When --log-file is used, const='.pyhunt.log' is automatically used
            updates["HUNT_LOG_FILE"] = args.log_file
            console.print(f"Log file set to '{updates['HUNT_LOG_FILE']}'")
        # Don't set default log file if not explicitly requested

    update_env_vars(updates)


if __name__ == "__main__":
    main()
