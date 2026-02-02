from __future__ import annotations

import asyncio
import os
from typing import List, Optional

from fastmcp import FastMCP
from pydantic import BaseModel

from obox_mcp import utils

# Initialize FastMCP server
mcp = FastMCP(
    "OboxNodeJS",
    instructions=(
        "A tool to manage Node.js environments and packages using fnm and pnpm in an asynchronous way. "
        "It supports installing Node.js versions, managing packages, and querying environment state."
    ),
)


class NodeEnvInfo(BaseModel):
    node_version: str
    pnpm_version: str
    installed_node_versions: List[str]
    project_name: Optional[str]


async def run_command_async(cmd: str, args: List[str]) -> str:
    """Helper to run commands asynchronously and return output."""
    try:
        process = await asyncio.create_subprocess_exec(
            cmd, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode().strip() or stdout.decode().strip()
            return f"Error executing {cmd} {' '.join(args)}: {error_msg}"

        return stdout.decode().strip()
    except Exception as e:
        return f"Error executing {cmd} {' '.join(args)}: {e!s}"


@mcp.tool(name="install_nodejs_tools")
async def install_nodejs_tools() -> str:
    """
    Installs fnm (Fast Node Manager) and pnpm.
    On macOS, uses Homebrew. On Windows, uses Scoop.
    """
    results = []

    # Install fnm
    success, msg = await utils.install_app("fnm")
    results.append(f"fnm: {msg}")

    # Install pnpm
    success, msg = await utils.install_app("pnpm")
    results.append(f"pnpm: {msg}")

    return "\n".join(results)


@mcp.tool(name="list_node_versions")
async def list_node_versions() -> str:
    """
    Lists all installed Node.js versions using 'fnm ls'.
    """
    return await run_command_async("fnm", ["ls"])


@mcp.tool(name="list_remote_node_versions")
async def list_remote_node_versions() -> str:
    """
    Lists available remote Node.js versions using 'fnm ls-remote'.
    """
    return await run_command_async("fnm", ["ls-remote"])


@mcp.tool(name="install_node_version")
async def install_node_version(version: str) -> str:
    """
    Installs a specific Node.js version using 'fnm install'.
    Example versions: '20', '18.17.0', 'latest'.
    """
    return await run_command_async("fnm", ["install", version])


@mcp.tool(name="use_node_version")
async def use_node_version(version: str) -> str:
    """
    Sets the current Node.js version using 'fnm use'.
    Note: This may require a shell restart or 'eval $(fnm env)' to reflect in some terminals.
    """
    return await run_command_async("fnm", ["use", version])


@mcp.tool(name="get_nodejs_info")
async def get_nodejs_info() -> str:
    """
    Retrieves detailed information about the current Node.js environment.
    """
    try:
        node_ver_task = run_command_async("node", ["--version"])
        pnpm_ver_task = run_command_async("pnpm", ["--version"])
        fnm_list_task = run_command_async("fnm", ["ls"])

        node_ver, pnpm_ver, fnm_list_raw = await asyncio.gather(
            node_ver_task, pnpm_ver_task, fnm_list_task
        )

        fnm_list = [line.strip() for line in fnm_list_raw.split('\n') if line.strip()]

        project_name = None
        if os.path.exists("package.json"):
            import json

            with open("package.json") as f:
                data = json.load(f)
                project_name = data.get("name")

        info = NodeEnvInfo(
            node_version=node_ver,
            pnpm_version=pnpm_ver,
            installed_node_versions=fnm_list,
            project_name=project_name,
        )
        return info.model_dump_json(indent=2)
    except Exception as e:
        return f"Error gathering environment info: {e!s}"


@mcp.tool(name="pnpm_add")
async def pnpm_add(package_name: str, dev: bool = False) -> str:
    """
    Installs a package using 'pnpm add'.
    Use dev=True for devDependencies.
    """
    args = ["add", package_name]
    if dev:
        args.append("-D")
    return await run_command_async("pnpm", args)


@mcp.tool(name="pnpm_install")
async def pnpm_install() -> str:
    """
    Installs all dependencies in package.json using 'pnpm install'.
    """
    return await run_command_async("pnpm", ["install"])


@mcp.tool(name="pnpm_run")
async def pnpm_run(script: str) -> str:
    """
    Runs a script defined in package.json using 'pnpm run <script>'.
    """
    return await run_command_async("pnpm", ["run", script])


if __name__ == "__main__":
    mcp.run()
