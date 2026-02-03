from __future__ import annotations

import asyncio
import os

from fastmcp import FastMCP

from obox_mcp import utils

mcp = FastMCP(
    "OboxFastAPI",
    instructions=(
        "A tool to initialize a new FastAPI project with uv. "
        "It sets up Python 3.12 and installs fastapi[standard]."
    ),
)


@mcp.tool(name="init_project")
async def init_project(path: str, python_version: str = "3.12") -> str:
    """
    Initializes a new FastAPI project at the specified path.
    Sets up uv environment with the specified Python version and installs fastapi[standard].

    Args:
        path: The absolute path where the project should be initialized.
        python_version: The Python version to use (default: "3.12").
    """
    if not os.path.isabs(path):
        # Try to make it absolute if it starts with ~
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            return "Error: Path must be absolute."

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    # 0. Ensure uv is installed
    success, msg = await utils.install_app("uv")
    if not success:
        return f"Error ensuring 'uv' is installed: {msg}"

    # 1. Check available python versions
    rc, stdout, stderr = await utils.run_command(["uv", "python", "list"])
    if rc != 0:
        return f"Error listing python versions: {stderr or stdout}"

    if python_version not in stdout:
        return (
            f"Error: Python version '{python_version}' not found in available versions.\n"
            f"Available versions:\n{stdout}"
        )

    # 2. uv init with specific python version
    rc, stdout, stderr = await utils.run_command(
        ["uv", "init", path, "--python", python_version]
    )
    if rc != 0:
        return f"Error during 'uv init': {stderr or stdout}"

    # 3. uv add "fastapi[standard]"
    rc, stdout, stderr = await utils.run_command(
        ["uv", "add", "fastapi[standard]"], cwd=path
    )
    if rc != 0:
        return f"Error during 'uv add fastapi[standard]': {stderr or stdout}"

    # 4. Create a basic main.py
    main_py_content = """from fastapi import FastAPI

app = FastAPI(title="Obox FastAPI Project")

@app.get("/")
async def root():
    return {"message": "Hello from Obox FastAPI"}
"""
    main_py_path = os.path.join(path, "main.py")
    if not os.path.exists(main_py_path):

        def write_file():
            with open(main_py_path, "w", encoding="utf-8") as f:
                f.write(main_py_content)

        await asyncio.to_thread(write_file)

    # Prepare the hint message and return
    return (
        f"\n🚀 FastAPI project successfully initialized at: {path}\n"
        f"Python {python_version} is set and fastapi[standard] is installed.\n"
        "A basic `main.py` has been created.\n\n"
        "💡 Next steps you might want to consider:\n"
        "1. Install database tools: `uv add sqlalchemy` or `uv add sqlmodel`\n"
        "2. Add authentication: `uv add pyjwt pwdlib[argon2]`\n"
        "3. Add settings management: `uv add pydantic-settings`\n"
        "4. Setup frontend: Create a React or Next.js project in a 'frontend' "
        "subdirectory.\n"
        "   Example: `npx create-next-app@latest frontend` (use pnpm "
        "if preferred)\n\n"
        "To run your app:\n"
        f"cd {path} && uv run fastapi dev main.py\n"
    )


if __name__ == "__main__":
    mcp.run()
