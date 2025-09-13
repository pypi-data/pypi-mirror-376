"""
Git interaction module for Git sensei.

This module provides an abstraction layer for Git command execution,
handling subprocess calls and returning structured results.
"""

import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitResult:
    """
    Structured result from Git command execution.

    Attributes:
        stdout: Standard output from the command
        stderr: Standard error output
        exit_code: Process exit code
        command: Original command that was executed
        success: Boolean indicating if command succeeded (exit_code == 0)
    """

    stdout: str
    stderr: str
    exit_code: int
    command: str
    success: bool


def is_git_available() -> bool:
    """
    Check if Git is installed and accessible.

    Returns:
        True if Git is available, False otherwise
    """
    return shutil.which("git") is not None


def get_git_version() -> Optional[str]:
    """
    Get installed Git version.

    Returns:
        Git version string if available, None if Git is not installed
    """
    if not is_git_available():
        return None

    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass

    return None


def execute_git_command(command: str, timeout: int = 30) -> GitResult:
    """
    Execute Git command and return structured result.

    Args:
        command: Git command string to execute
        timeout: Maximum time to wait for command completion in seconds

    Returns:
        GitResult object with execution details
    """
    # Check if Git is available before attempting execution
    if not is_git_available():
        return GitResult(
            stdout="",
            stderr="Git is not installed or not available in PATH. Please install "
            "Git and ensure it's accessible from the command line.",
            exit_code=127,  # Command not found exit code
            command=command,
            success=False,
        )

    # Validate command input
    if not command or not command.strip():
        return GitResult(
            stdout="",
            stderr="Empty command provided. Please specify a Git command to "
            "execute.",
            exit_code=1,
            command=command,
            success=False,
        )

    # Parse command string into list for subprocess
    # Remove 'git' prefix if present since we'll add it
    try:
        cmd_parts = command.strip().split()
        if cmd_parts and cmd_parts[0].lower() == "git":
            cmd_parts = cmd_parts[1:]

        # Validate that we have at least one command part
        if not cmd_parts:
            return GitResult(
                stdout="",
                stderr="Invalid Git command format. Command cannot be empty after "
                "removing 'git' prefix.",
                exit_code=1,
                command=command,
                success=False,
            )

        # Construct full command
        full_command = ["git"] + cmd_parts

    except Exception as e:  # pylint: disable=broad-exception-caught
        return GitResult(
            stdout="",
            stderr=f"Error parsing command '{command}': {str(e)}",
            exit_code=1,
            command=command,
            success=False,
        )

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        return GitResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            command=command,
            success=result.returncode == 0,
        )

    except subprocess.TimeoutExpired:
        return GitResult(
            stdout="",
            stderr=f"Command timed out after {timeout} seconds. The Git operation "
            "may be taking too long or may be waiting for input.",
            exit_code=124,  # Standard timeout exit code
            command=command,
            success=False,
        )
    except FileNotFoundError:
        return GitResult(
            stdout="",
            stderr="Git executable not found. Please ensure Git is installed and "
            "available in your system PATH.",
            exit_code=127,  # Command not found exit code
            command=command,
            success=False,
        )
    except PermissionError:
        return GitResult(
            stdout="",
            stderr="Permission denied when trying to execute Git command. Check "
            "file permissions and repository access rights.",
            exit_code=126,  # Permission denied exit code
            command=command,
            success=False,
        )
    except OSError as e:
        return GitResult(
            stdout="",
            stderr=f"System error occurred while executing Git command: " f"{str(e)}",
            exit_code=1,
            command=command,
            success=False,
        )
    except subprocess.SubprocessError as e:
        return GitResult(
            stdout="",
            stderr=f"Subprocess error occurred: {str(e)}",
            exit_code=1,
            command=command,
            success=False,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        return GitResult(
            stdout="",
            stderr=f"Unexpected error occurred while executing Git command: "
            f"{str(e)}",
            exit_code=1,
            command=command,
            success=False,
        )
