from __future__ import annotations

import os
import platform

from fastmcp import FastMCP

from obox_mcp import utils

# Initialize FastMCP server for Just
mcp = FastMCP(
    "OboxProjectRunner",
    instructions=(
        "Auto-detects tasks and finalizes setup. Call after project creation. "
        "The agent should modify the generated justfile to fit the project needs."
    ),
)


async def detect_projects(base_path: str) -> list[tuple[str, str, str]]:
    """
    Detect projects in base_path recursively using fd.
    Returns list of (rel_path, type, name).
    """
    projects = []

    # Ensure fd is installed
    success, _ = await utils.install_app("fd")
    if not success:
        return []

    patterns = ["pyproject.toml", "package.json", ".*\\.csproj$", ".*\\.sln$"]
    regex = "^(" + "|".join(patterns) + ")$"

    cmd = [
        "fd",
        "-t",
        "f",
        "--max-depth",
        "3",
        "--exclude",
        "node_modules",
        "--exclude",
        "venv",
        "--exclude",
        ".venv",
        "--exclude",
        ".git",
        regex,
        base_path,
    ]

    output = await utils.run_command_output(cmd, error_prefix="fd error")
    if output.startswith("fd error"):
        return []

    found_paths = output.splitlines()
    seen_dirs = set()

    for p in found_paths:
        dirname = os.path.dirname(p)
        rel_dir = os.path.relpath(dirname, base_path)

        if rel_dir in seen_dirs:
            continue

        filename = os.path.basename(p)
        p_type = None
        if filename == "pyproject.toml":
            p_type = "python"
        elif filename == "package.json":
            p_type = "nodejs"
        elif filename.endswith((".csproj", ".sln")):
            p_type = "dotnet"

        if p_type:
            name = os.path.basename(dirname) if rel_dir != "." else "root"
            projects.append((rel_dir, p_type, name))
            seen_dirs.add(rel_dir)

    return projects


@mcp.tool(name="project_runner")
async def project_runner() -> str:
    """
    Finalizes project setup by detecting structure.
    Call this tool immediately after creating any new project.
    """
    abs_path = os.getcwd()

    # 1. Install just
    success, msg = await utils.install_app("just")
    if not success:
        return f"Error installing 'just': {msg}"

    # 2. Detect projects
    try:
        projects = await detect_projects(abs_path)
    except Exception as e:
        return f"Error detecting projects: {e!s}"

    if not projects:
        return "No supported project structure detected (pyproject.toml, package.json, or .csproj/.sln)."  # noqa: E501

    # 3. Generate justfile
    system = platform.system()
    if system == "Windows":
        shell_setting = 'set shell := ["powershell", "-Command"]'
        sep = ";"
    else:
        shell_setting = 'set shell := ["bash", "-c"]'
        sep = "&&"

    justfile_content = [
        shell_setting,
        '',
    ]

    dev_tasks = []

    for rel_path, p_type, name in projects:
        # Determine unique task name
        if name == "root":
            if len(projects) > 1:
                # Use project type for root if multiple projects to avoid 'dev' conflict
                task_name = "backend" if p_type == "python" else p_type
            else:
                task_name = "dev"
        else:
            task_name = name

        # Ensure task name is unique
        base_task_name = task_name
        counter = 1
        while task_name in dev_tasks:
            task_name = f"{base_task_name}-{counter}"
            counter += 1

        if p_type == "python":
            justfile_content.append(f"@{task_name}:")
            # For python, check if main.py exists
            p_abs_path = os.path.join(abs_path, rel_path)
            if os.path.exists(os.path.join(p_abs_path, "main.py")):
                justfile_content.append(f"    cd {rel_path} {sep} uv run main.py")
            else:
                justfile_content.append(f"    cd {rel_path} {sep} uv sync")
            dev_tasks.append(task_name)
        elif p_type == "nodejs":
            justfile_content.append(f"@{task_name}:")
            justfile_content.append(f"    cd {rel_path} {sep} pnpm dev")
            dev_tasks.append(task_name)
        elif p_type == "dotnet":
            # Dotnet uses 'run' by default
            d_task = task_name if task_name != "dev" else "run"
            justfile_content.append(f"@{d_task}:")
            justfile_content.append(f"    cd {rel_path} {sep} dotnet run")
            dev_tasks.append(d_task)
        justfile_content.append("")

    # Add a parallel task if multiple dev tasks exist
    if len(dev_tasks) > 1:
        justfile_content.append("[parallel]")
        justfile_content.append(f"dev: {' '.join(dev_tasks)}")
        justfile_content.append("")

    justfile_content.append("default:\n    just --list")

    # 4. Write justfile
    justfile_output_path = os.path.join(abs_path, "justfile")
    try:
        with open(justfile_output_path, "w") as f:
            f.write("\n".join(justfile_content))
    except Exception as e:
        return f"Error writing justfile: {e!s}"

    task_list = "\n".join([f"- `just {t}`" for t in dev_tasks])
    all_dev_msg = (
        "\n- `just dev` (run all detected projects in parallel)"
        if len(dev_tasks) > 1
        else ""
    )

    return (
        f"Successfully created 'justfile' at {justfile_output_path}.\n\n"
        "### Available Tasks:\n"
        f"{task_list}"
        f"{all_dev_msg}"
        "\n\n### How to run:\n"
        "1. Open your terminal in the project root.\n"
        "2. Run `just <task_name>` to execute a task.\n"
        "3. Run `just` or `just --list` to see all available tasks.\n"
        "4. **IMPORTANT**: Review the generated `justfile` and modify it if your "
        "project requires additional tasks or specific build flags.\n"
    )


if __name__ == "__main__":
    mcp.run()
