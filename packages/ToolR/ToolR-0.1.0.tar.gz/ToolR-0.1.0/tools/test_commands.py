"""Test command to verify signature parsing works."""

from __future__ import annotations

import enum
import pathlib
from typing import Annotated

from toolr import Context
from toolr import command_group
from toolr.utils._argument import bool_arg
from toolr.utils._argument import int_arg
from toolr.utils._argument import string_arg


class LogLevel(enum.Enum):
    """Log level enum for testing."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Color(enum.Enum):
    """Color enum for testing."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


# Create a test command group
test_group = command_group("test", "Test Commands", "Commands for testing signature parsing")


@test_group.command("hello", help="Say hello with optional name")
def hello_command(
    ctx: Context,
    name: Annotated[str, string_arg(help_text="Name to greet")] = "World",
    count: Annotated[int, int_arg(help_text="Number of times to greet", aliases=["-c"])] = 1,
    uppercase: Annotated[bool, bool_arg(help_text="Use uppercase")] = False,
) -> str:
    """Say hello to someone."""
    greeting = f"Hello, {name}!"
    if uppercase:
        greeting = greeting.upper()

    result = []
    for _ in range(count):
        result.append(greeting)

    return "\n".join(result)


@test_group.command("copy", help="Copy a file (positional test)")
def copy_command(
    ctx: Context,
    source: Annotated[str, string_arg(help_text="Source file path")],
    destination: Annotated[str, string_arg(help_text="Destination file path")],
) -> str:
    """Copy a file from source to destination."""
    # This is just a test command, don't actually copy
    return f"Would copy {source} to {destination}"


@test_group.command("add", help="Add two numbers")
def add_command(
    ctx: Context,
    x: Annotated[int, int_arg(help_text="First number")],
    y: Annotated[int, int_arg(help_text="Second number")],
    verbose: Annotated[bool, bool_arg(help_text="Show calculation", aliases=["-v"])] = False,
) -> str:
    """Add two numbers together."""
    result = x + y
    if verbose:
        return f"{x} + {y} = {result}"
    return str(result)


@test_group.command("simple", help="Simple command without annotations")
def simple_command(ctx: Context, message: str = "default message") -> str:
    """A simple command that uses type inference."""
    return f"Message: {message}"


@test_group.command("bool-test", help="Test boolean parameter handling")
def bool_test_command(
    ctx: Context,
    debug: Annotated[bool, bool_arg(help_text="Enable debug mode")] = False,
    verbose: bool = False,
    count: int = 1,
) -> str:
    """Test how boolean parameters are handled."""
    return f"verbose={verbose}, debug={debug}, count={count}"


@test_group.command("path-test", help="Test pathlib.Path parameter handling")
def path_test_command(
    ctx: Context,
    input_file: pathlib.Path,
    output_dir: pathlib.Path = pathlib.Path("./output"),
    create_dirs: bool = False,
) -> str:
    """Test how pathlib.Path parameters are handled."""
    return (
        f"input_file={input_file} (type={type(input_file)}), "
        f"output_dir={output_dir} (type={type(output_dir)}), "
        f"create_dirs={create_dirs}"
    )


@test_group.command("enum-test", help="Test enum parameter handling")
def enum_test_command(
    ctx: Context,
    log_level: LogLevel,
    color: Color = Color.BLUE,
    verbose: bool = False,
) -> str:
    """Test how enum parameters are handled."""
    return (
        f"log_level={log_level.value} (type={type(log_level)}), "
        f"color={color.value} (type={type(color)}), verbose={verbose}"
    )
