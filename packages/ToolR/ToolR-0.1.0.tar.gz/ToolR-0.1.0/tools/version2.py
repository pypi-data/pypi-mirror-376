"""
ToolR versioning utilities.
"""

from __future__ import annotations

from typing import Annotated

from packaging.version import Version

from toolr import Context
from toolr import arg
from toolr import command_group

group = command_group("version", "Versioning utilities", docstring=__doc__)


def _current_version(ctx: Context) -> str:
    ret = ctx.run("uv", "version", "--short", capture_output=True, stream_output=False)
    return Version(ret.stdout.read().rstrip())


def _git_describe(ctx: Context) -> tuple[Version, int, str]:
    ret = ctx.run("git", "describe", "--tags", "--long", capture_output=True, stream_output=False)
    version, distance_to_latest_tag, short_commit_hash = ret.stdout.read().rstrip().split("-")
    return Version(version), int(distance_to_latest_tag), short_commit_hash


def _commits_since_last_tag(ctx: Context) -> int:
    ret = ctx.run("git", "rev-list", "HEAD", "--count", "..@(tag:v*)", capture_output=True, stream_output=False)
    return int(ret.stdout.read().rstrip())


@group.command
def current(ctx: Context) -> None:
    """
    Get the current version of ToolR.
    """
    ctx.print(_current_version(ctx))


@group.command
def next_dev(ctx: Context) -> str:
    """
    Get the next development version of ToolR.
    """
    current_version, distance_to_latest_tag, short_commit_hash = _git_describe(ctx)
    new_version = Version(
        f"{current_version.major}.{current_version.minor + 1}.{current_version.micro}.dev{distance_to_latest_tag}"
    )
    ctx.print(new_version)


@group.command
def bump(
    ctx: Context,
    new_version: Annotated[str | None, arg(nargs="?")],
    major: Annotated[bool, arg(group="version")] = False,
    minor: Annotated[bool, arg(group="version")] = False,
    patch: Annotated[bool, arg(group="version")] = False,
    dev: Annotated[bool, arg(group="version")] = False,
) -> None:
    """
    Bump the version of ToolR.

    Args:
        major: Whether to bump the major version.
        minor: Whether to bump the minor version.
        patch: Whether to bump the patch version.
        dev: Whether to bump the version for a development version.
        new_version: The version to bump to.
    """
    if new_version is None and not any([major, minor, patch, dev]):
        ctx.error("Must pass the NEW_VERSION or one of --major/--minor/--patch/--dev")
        ctx.exit(1)
    elif new_version is not None and any([major, minor, patch, dev]):
        ctx.error("Cannot specify both NEW_VERSION and any of --major/--minor/--patch/--dev")
        ctx.exit(1)

    if new_version is not None:
        version = Version(new_version)
    else:
        current_version, distance_to_latest_tag, short_commit_hash = _git_describe(ctx)
        major_version = current_version.major
        minor_version = current_version.minor
        patch_version = current_version.micro
        dev_version = ""
        if dev:
            minor_version += 1
            dev_version = f".dev{distance_to_latest_tag}"
        elif major:
            major_version += 1
        elif minor:
            minor_version += 1
        elif patch:
            patch_version += 1
        else:
            ctx.error("Must specify either dev, major, minor, or patch")
            ctx.exit(1)

        version = Version(f"{major_version}.{minor_version}.{patch_version}{dev_version}")
    ctx.print(version)


@group.command
def commit(ctx: Context, version: str) -> None:
    """
    Commit the version of ToolR.

    Args:
        version: The version to commit.
    """
    ctx.run("git", "commit", "-m", f"Bump version to {version}")
    ctx.run("git", "tag", version)
