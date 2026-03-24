import json
import subprocess
from dataclasses import dataclass


@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    url: str
    state: str
    created_at: str


def get_open_prs(remote_url: str) -> list[PullRequest]:
    repo_slug = _extract_repo_slug(remote_url)
    if not repo_slug:
        return []
    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--repo", repo_slug, "--state", "open",
             "--json", "number,title,author,url,state,createdAt", "--limit", "20"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        return [
            PullRequest(
                number=pr["number"],
                title=pr["title"],
                author=pr.get("author", {}).get("login", "unknown"),
                url=pr["url"],
                state=pr["state"],
                created_at=pr["createdAt"][:10],
            )
            for pr in data
        ]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []


def _extract_repo_slug(remote_url: str) -> str | None:
    if not remote_url:
        return None
    url = remote_url.strip()
    # SSH format: git@github.com:owner/repo.git
    if url.startswith("git@github.com:"):
        slug = url.replace("git@github.com:", "").removesuffix(".git")
        return slug
    # HTTPS format: https://github.com/owner/repo.git
    if "github.com/" in url:
        parts = url.split("github.com/")[-1].removesuffix(".git")
        return parts
    return None
