# DevShelf

A lightweight, local web dashboard for browsing your git repositories and Markdown documents. No cloud services, no database — just a fast overview of what's on your machine.

## What It Does

**Repo Browser** — Scans a source directory (default `~/src`) and discovers all git repositories, including those nested in subdirectories. For each repo you can see:

- Current and default branch
- All local and remote branches
- Recent commits on the default branch
- Open pull requests (via GitHub CLI)
- Rendered README

**Doc Browser** — Browses configured directories for Markdown files and renders them with syntax highlighting, tables, and a table of contents.

## Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Frontend**: Alpine.js (CDN), vanilla CSS with light/dark theme
- **GitHub Integration**: `gh` CLI (optional, for pull requests)
- **No build step** — no bundler, no node_modules

## Getting Started

### Prerequisites

- Python 3.10+
- Git
- [GitHub CLI](https://cli.github.com/) (optional, for PR data)

### Install

```bash
git clone https://github.com/ChrisWHendricks/devshelf.git
cd devshelf
pip install -e .
```

### Run

```bash
devshelf
```

This starts the server at `http://127.0.0.1:8400` and scans `~/src` for repositories.

### CLI Options

```
devshelf --dir ~/projects          # Scan a different directory
devshelf --md-dir ~/notes          # Add a Markdown directory (repeatable)
devshelf --port 9000               # Use a different port
devshelf --host 0.0.0.0            # Bind to all interfaces
devshelf --config my-config.yaml   # Use a custom config file
```

## Configuration

Create a `config.yaml` in the working directory:

```yaml
# Parent directory to scan for git repositories
src_dir: ~/src

# Directories containing Markdown files to browse
md_dirs:
  - ~/docs
  - ~/notes

# Server settings
host: 127.0.0.1
port: 8400
```

CLI flags override config file values.

## How It Works

1. **Repo discovery** recursively walks the source directory looking for `.git` folders. Subdirectories that contain repos are shown as expandable groups in the sidebar.

2. **Repo detail** shells out to `git` to read branches, commits, and remote URLs. The README is rendered server-side using Python-Markdown with fenced code blocks, syntax highlighting, and table support. HTML output is sanitized to strip scripts and event handlers.

3. **Pull requests** are fetched lazily when a repo is selected, using `gh pr list` against the repo's remote. No API token configuration is needed if `gh` is already authenticated.

4. **Doc browser** builds a file tree from the configured Markdown directories and renders files on demand through the same Markdown pipeline.

## Project Structure

```
code_registry/
  cli.py              # Typer CLI entry point
  config.py           # YAML config loading
  main.py             # FastAPI app and API routes
  git_service.py      # Git repo discovery and info
  github_service.py   # GitHub PR fetching via gh CLI
  markdown_service.py # Markdown rendering and sanitization
  static/
    index.html        # Single-page app (Alpine.js)
    js/app.js         # Frontend logic
    css/style.css     # Component-based CSS with light/dark themes
    img/github.svg    # GitHub icon
```

## License

MIT
