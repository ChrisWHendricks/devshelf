from pathlib import Path

import re

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension


_md = markdown.Markdown(extensions=[
    FencedCodeExtension(),
    CodeHiliteExtension(css_class="highlight", guess_lang=False),
    TableExtension(),
    TocExtension(),
    "md_in_html",
])

_DANGEROUS_TAGS = re.compile(
    r'<\s*\/?\s*(script|iframe|object|embed|form|input|textarea|button|link|meta|base|applet)'
    r'[^>]*>',
    re.IGNORECASE,
)
_EVENT_HANDLERS = re.compile(r'\bon\w+\s*=', re.IGNORECASE)


def _sanitize_html(html: str) -> str:
    html = _DANGEROUS_TAGS.sub('', html)
    html = _EVENT_HANDLERS.sub('data-removed=', html)
    return html


def render_markdown(text: str) -> str:
    _md.reset()
    return _sanitize_html(_md.convert(text))


def find_repo_readme(repo_path: Path) -> tuple[str | None, str | None]:
    """Returns (filename, rendered_html) or (None, None)."""
    # Check common README names
    for name in ("README.md", "ReadMe.md", "readme.md", "Readme.md"):
        candidate = repo_path / name
        if candidate.is_file():
            return name, render_markdown(candidate.read_text(errors="replace"))

    # Fall back to any .md file in root
    md_files = sorted(repo_path.glob("*.md"))
    if md_files:
        f = md_files[0]
        return f.name, render_markdown(f.read_text(errors="replace"))

    return None, None


def build_md_tree(md_dirs: list[Path]) -> list[dict]:
    """Build a nested tree structure of markdown directories."""
    trees = []
    for md_dir in md_dirs:
        if not md_dir.is_dir():
            continue
        tree = _scan_dir(md_dir, md_dir)
        if tree:
            trees.append(tree)
    return trees


def _scan_dir(dir_path: Path, root: Path) -> dict | None:
    children = []
    files = []

    for entry in sorted(dir_path.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            subtree = _scan_dir(entry, root)
            if subtree:
                children.append(subtree)
        elif entry.suffix.lower() == ".md":
            files.append({
                "type": "file",
                "name": entry.name,
                "path": str(entry),
            })

    if not children and not files:
        return None

    return {
        "type": "directory",
        "name": dir_path.name,
        "path": str(dir_path),
        "children": children + files,
    }


def render_md_file(file_path: str, md_dirs: list[Path]) -> str | None:
    """Render a markdown file, but only if it's under an allowed md_dir."""
    target = Path(file_path).resolve()
    allowed = any(
        target == d.resolve() or d.resolve() in target.parents
        for d in md_dirs
    )
    if not allowed:
        return None
    if not target.is_file() or target.suffix.lower() != ".md":
        return None
    return render_markdown(target.read_text(errors="replace"))
