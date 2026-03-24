import subprocess
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CommitInfo:
    sha: str
    message: str
    author: str
    date: str


@dataclass
class RepoInfo:
    name: str
    path: str
    current_branch: str
    branches: list[dict]  # [{name, is_current, is_remote}]
    remote_url: str
    default_branch: str
    last_commits: list[CommitInfo]


def _run_git(repo_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True, text=True, timeout=10,
    )
    return result.stdout.strip()


def discover_repos(src_dir: Path) -> list[str]:
    if not src_dir.is_dir():
        return []
    repos = []
    _scan_for_repos(src_dir, src_dir, repos)
    return sorted(repos)


def _scan_for_repos(dir_path: Path, root: Path, repos: list[str]) -> None:
    for entry in sorted(dir_path.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if (entry / ".git").is_dir():
            repos.append(str(entry.relative_to(root)))
        else:
            _scan_for_repos(entry, root, repos)


def get_repo_info(src_dir: Path, repo_rel_path: str) -> RepoInfo:
    repo_name = repo_rel_path.split("/")[-1]
    repo_path = src_dir / repo_rel_path

    current_branch = _run_git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")

    default_branch = _detect_default_branch(repo_path)

    branches = _get_branches(repo_path, current_branch)

    remote_url = _run_git(repo_path, "config", "--get", "remote.origin.url")

    last_commits = _get_commits(repo_path, default_branch, 5)

    return RepoInfo(
        name=repo_name,
        path=str(repo_path),
        current_branch=current_branch,
        branches=branches,
        remote_url=remote_url,
        default_branch=default_branch,
        last_commits=last_commits,
    )


def _detect_default_branch(repo_path: Path) -> str:
    ref = _run_git(repo_path, "symbolic-ref", "refs/remotes/origin/HEAD")
    if ref:
        return ref.replace("refs/remotes/origin/", "")
    # fallback
    for candidate in ("main", "master"):
        check = _run_git(repo_path, "rev-parse", "--verify", f"refs/heads/{candidate}")
        if check:
            return candidate
    return "main"


def _get_branches(repo_path: Path, current_branch: str) -> list[dict]:
    raw = _run_git(repo_path, "branch", "-a", "--format=%(refname:short)")
    if not raw:
        return []
    branches = []
    seen = set()
    for line in raw.splitlines():
        name = line.strip()
        if not name or name.endswith("/HEAD"):
            continue
        is_remote = name.startswith("origin/")
        display_name = name
        if display_name in seen:
            continue
        seen.add(display_name)
        branches.append({
            "name": display_name,
            "is_current": name == current_branch,
            "is_remote": is_remote,
        })
    return branches


def _get_commits(repo_path: Path, branch: str, count: int) -> list[CommitInfo]:
    fmt = "%H%n%s%n%an%n%ai"
    raw = _run_git(repo_path, "log", branch, f"-{count}", f"--format={fmt}")
    if not raw:
        return []
    lines = raw.splitlines()
    commits = []
    for i in range(0, len(lines), 4):
        if i + 3 >= len(lines):
            break
        commits.append(CommitInfo(
            sha=lines[i][:8],
            message=lines[i + 1],
            author=lines[i + 2],
            date=lines[i + 3][:10],
        ))
    return commits
