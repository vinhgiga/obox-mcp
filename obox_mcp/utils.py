from __future__ import annotations

import asyncio
import platform
import shutil
import sys


async def is_command_exists(command: str) -> bool:
    """
    Check if a command exists on the system PATH asynchronously.
    """
    return await asyncio.to_thread(shutil.which, command) is not None


async def run_command(command: str) -> tuple[int, str, str]:
    """
    Run a shell command asynchronously and return returncode, stdout, and stderr.
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode().strip(), stderr.decode().strip()


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
            '-Scope CurrentUser; Invoke-RestMethod -Uri https://get.scoop.sh | '
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


if __name__ == "__main__":
    # Example usage if run directly
    if len(sys.argv) > 1:
        app = sys.argv[1]
        bucket = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(install_app(app, bucket))
    else:
        print("Usage: python utils.py <app_name> [scoop_bucket]")
