"""Utility functions for call-helper."""

import os
import subprocess


def run_command(cmd):
    """Execute a shell command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def read_file(path):
    """Read file contents."""
    f = open(path, "r")
    content = f.read()
    return content


def get_temp_dir():
    """Get temporary directory path."""
    tmp = os.environ.get("TEMP", "/tmp")
    return tmp


def format_duration(seconds):
    """Format seconds into human readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m"
