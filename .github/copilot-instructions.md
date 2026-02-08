# Obox Development Instructions

You are an expert developer assistant equipped with **Obox MCP Tools**. Follow these instructions to efficiently build and manage projects.

## 🛠 Obox MCP Tools

You have access to a suite of tools for automation. Use them proactively:

- **Project Runner**: After creating or modifying a project structure, ALWAYS call `just_project_runner` to generate or update the `justfile`.
- **Environment Management**:
  - Python: Use `python_*` tools. Always use `uv` for package management.
  - Node.js: Use `nodejs_*` tools. Always use `pnpm`.
  - .NET: Use `dotnet_*` tools.
- **Search & Inspection**: Use `ripgrep_search`, `fd_find`, and `bat_read_file` for efficient codebase exploration.

## 🐍 Python Guidelines

- **Package Manager**: Use `astral uv`. Never use `pip` directly unless `uv` is unavailable.
- **Execution**: Run scripts using `uv run`.
- **Programming Style**: Always use `asyncio` for asynchronous programming.
- **Frameworks**: Use `FastAPI` for APIs, `FastMCP` for MCP servers, and `Pydantic AI` for agentic logic.

## 📦 Web Development Guidelines

- **Package Manager**: Use `pnpm`. Avoid `npm` or `yarn`.
- **Tech Stack**: Base projects on Vite/React with TypeScript by default unless specified otherwise.
- **Styling**: Prefer Tailwind CSS or Vanilla CSS as per project requirements.

## 🏗 Project Workflow

1. **Initialize**: Use `*_init_project` tools to scaffold new projects.
2. **Sync**: Run `python_uv_sync` or `nodejs_pnpm_install` after adding dependencies.
3. **Finalize**: Call `just_project_runner` to set up the `justfile`.
4. **Run**: Use `just <task>` for development and testing.

## 📚 Documentation

- Always use **Context7 MCP** to fetch up-to-date library/API documentation and code examples.
- Do not guess API signatures; query Context7 if unsure.
