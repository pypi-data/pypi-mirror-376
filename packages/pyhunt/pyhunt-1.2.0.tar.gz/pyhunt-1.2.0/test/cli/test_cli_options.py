import os
import tempfile
import subprocess
import pytest


@pytest.fixture
def temp_log_file():
    with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def example_script():
    script = """
from pyhunt import trace, logger

@trace
def test_function():
    logger.info("Test message")
    return "success"

if __name__ == "__main__":
    result = test_function()
    print(f"Result: {result}")
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
        f.write(script)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


def run_command(cmd, env_vars=None):
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    return subprocess.run(cmd, capture_output=True, text=True, cwd=".", env=env)


@pytest.mark.parametrize(
    "args, expected",
    [
        (["--color", "true"], "Color output set to 'true'"),
        (["--color", "false"], "Color output set to 'false'"),
    ],
)
def test_color_option(args, expected):
    result = run_command(["uv", "run", "hunt"] + args)
    assert result.returncode == 0
    assert expected in result.stdout


@pytest.mark.parametrize("color", ["true", "false"])
def test_color_functionality(example_script, color):
    run_command(["uv", "run", "hunt", "--color", color])
    result = run_command(["uv", "run", "python", example_script], {"HUNT_COLOR": color})
    assert result.returncode == 0
    assert "Result: success" in result.stdout


def test_log_file_option(temp_log_file):
    result = run_command(["uv", "run", "hunt", "--log-file", temp_log_file])
    assert result.returncode == 0
    assert f"Log file set to '{temp_log_file}'" in result.stdout
    assert os.path.exists(temp_log_file)


@pytest.mark.parametrize(
    "color, expect_emoji",
    [
        ("true", True),
        ("false", False),
    ],
)
def test_emoji_behavior(color, expect_emoji):
    script = """
import os
os.environ['HUNT_COLOR'] = '{color}'
os.environ['HUNT_LEVEL'] = 'DEBUG'
from pyhunt import trace

@trace
def test_emoji_function():
    return "test"
if __name__ == "__main__":
    test_emoji_function()
""".format(color=color)

    script_path = f"test_emoji_{color}.py"
    try:
        with open(script_path, "w") as f:
            f.write(script)

        result = run_command(["python", script_path])
        assert result.returncode == 0

        if expect_emoji:
            assert any(e in result.stdout for e in ["🟢", "🔳", "🟥"])
        else:
            assert "🟢" not in result.stdout
            assert "→" in result.stdout or "←" in result.stdout
    finally:
        if os.path.exists(script_path):
            os.unlink(script_path)
