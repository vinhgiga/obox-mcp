from __future__ import annotations

import asyncio
import os
import platform
import shutil
import sys


async def is_command_exists(command: str) -> bool:
    """
    Check if a command exists on the system PATH asynchronously.
    """
    return await asyncio.to_thread(shutil.which, command) is not None


async def run_command(
    command: str | list[str], input_data: str | None = None, cwd: str | None = None
) -> tuple[int, str, str]:
    """
    Run a shell command or a process with arguments asynchronously.
    Returns returncode, stdout, and stderr.
    """
    if isinstance(command, str):
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE if input_data is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
    else:
        process = await asyncio.create_subprocess_exec(
            command[0],
            *command[1:],
            stdin=asyncio.subprocess.PIPE if input_data is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )

    stdout, stderr = await process.communicate(
        input=input_data.encode() if input_data is not None else None
    )
    return process.returncode, stdout.decode().strip(), stderr.decode().strip()


async def run_command_output(
    command: str | list[str],
    input_data: str | None = None,
    error_prefix: str = "Error executing",
    success_codes: list[int] | None = None,
    cwd: str | None = None,
) -> str:
    """
    Run a command and return its stdout or a formatted error message if it fails.
    """
    if success_codes is None:
        success_codes = [0]

    try:
        code, out, err = await run_command(command, input_data, cwd=cwd)
    except Exception as e:
        cmd_str = command if isinstance(command, str) else " ".join(command)
        return f"{error_prefix} {cmd_str}: {e!s}"
    else:
        if code in success_codes:
            return out

        cmd_str = command if isinstance(command, str) else " ".join(command)
        msg = err or out
        return f"{error_prefix} {cmd_str}: {msg}"


async def find_project_root(filename: str) -> str | None:
    """
    Find the directory containing filename by searching upwards from current dir,
    and then downwards using fd if not found.
    """
    current = os.getcwd()
    # Search upwards
    while True:
        if os.path.exists(os.path.join(current, filename)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Fallback to fd if available
    if await is_command_exists("fd"):
        code, out, err = await run_command(
            ["fd", "-H", "-I", "-t", "f", f"^{filename}$", "--max-depth", "5"]
        )
        if code == 0 and out:
            # Get the first match and return its directory
            first_match = out.splitlines()[0]
            return os.path.dirname(os.path.abspath(first_match))

    return None


async def install_package_manager() -> tuple[bool, str]:
    """
    Install Homebrew on macOS or Scoop on Windows.
    """
    system = platform.system()

    if system == "Darwin":
        if await is_command_exists("brew"):
            return True, "Homebrew is already installed."

        print("Installing Homebrew...")
        # Official Homebrew installation script
        cmd = (
            '/bin/bash -c "$(curl -fsSL '
            'https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        code, out, err = await run_command(cmd)
        if code == 0:
            return True, "Homebrew installed successfully."
        return False, f"Failed to install Homebrew: {err or out}"

    if system == "Windows":
        if await is_command_exists("scoop"):
            return True, "Scoop is already installed."

        print("Installing Scoop...")
        # Official Scoop installation command via PowerShell
        ps_cmd = (
            'powershell -Command "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned '
            "-Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | "
            'Invoke-Expression"'
        )
        code, out, err = await run_command(ps_cmd)
        if code == 0:
            return True, "Scoop installed successfully."
        return False, f"Failed to install Scoop: {err or out}"

    return False, f"Unsupported OS for automatic package manager installation: {system}"


async def add_scoop_bucket(bucket_name: str) -> tuple[bool, str]:
    """
    Add a bucket to Scoop (Windows only).
    """
    if platform.system() != "Windows":
        return False, "Scoop buckets can only be added on Windows."

    # Ensure scoop is installed first
    success, msg = await install_package_manager()
    if not success:
        return False, msg

    print(f"Adding Scoop bucket: {bucket_name}...")
    code, out, err = await run_command(f"scoop bucket add {bucket_name}")

    # Often returns error 1 if bucket already exists, we should check the message
    if code == 0 or "already added" in out.lower() or "already added" in err.lower():
        return True, f"Bucket '{bucket_name}' is ready."

    return False, f"Failed to add Scoop bucket: {err or out}"


async def install_app(
    app_name: str, scoop_bucket: str | None = None
) -> tuple[bool, str]:
    """
    Check if app is installed, if not, install package manager and then the app.
    """
    # 1. Check if command already exists
    if await is_command_exists(app_name):
        return True, f"'{app_name}' is already installed and available on PATH."

    # 2. Ensure package manager is installed
    success, msg = await install_package_manager()
    if not success:
        return False, f"Installation failed: {msg}"

    system = platform.system()

    # 3. Handle Scoop bucket if provided
    if system == "Windows" and scoop_bucket:
        b_success, b_msg = await add_scoop_bucket(scoop_bucket)
        if not b_success:
            print(f"Warning: {b_msg}")

    # 4. Install the app
    print(f"Installing {app_name}...")
    if system == "Darwin":
        install_cmd = f"brew install {app_name}"
    elif system == "Windows":
        install_cmd = f"scoop install {app_name}"
    else:
        return False, f"Unsupported OS: {system}"

    code, out, err = await run_command(install_cmd)
    if code == 0:
        return True, f"Successfully installed {app_name}."

    return False, f"Failed to install {app_name}: {err or out}"


async def search_package(name: str) -> tuple[bool, str]:
    """
    Search for a package using the system's package manager.
    - On macOS: brew search {name}
    - On Windows: scoop search {name}
    """
    system = platform.system()
    if system == "Darwin":
        cmd = f"brew search {name}"
    elif system == "Windows":
        cmd = f"scoop search {name}"
    else:
        return False, f"Unsupported OS for package search: {system}"

    code, out, err = await run_command(cmd)
    if code == 0:
        return True, out
    return False, f"Failed to search for {name}: {err or out}"


if __name__ == "__main__":
    # Example usage if run directly
    if len(sys.argv) > 1:
        app = sys.argv[1]
        bucket = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(install_app(app, bucket))
    else:
        print("Usage: python utils.py <app_name> [scoop_bucket]")
