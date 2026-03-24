from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import Config
from . import git_service, github_service, markdown_service


def _validate_repo_name(repo_name: str) -> None:
    if not repo_name or "\\" in repo_name or ".." in repo_name or repo_name.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid repository name")


def create_app(config: Config) -> FastAPI:
    app = FastAPI(title="DevShelf")

    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def index():
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/api/repos")
    async def list_repos():
        repos = git_service.discover_repos(config.src_dir)
        return {"repos": repos, "src_dir": str(config.src_dir)}

    @app.get("/api/repos/{repo_name:path}")
    async def get_repo(repo_name: str):
        _validate_repo_name(repo_name)

        # Strip /prs suffix and redirect to PR handler
        if repo_name.endswith("/prs"):
            return await get_repo_prs(repo_name[:-4])

        repos = git_service.discover_repos(config.src_dir)
        if repo_name not in repos:
            raise HTTPException(status_code=404, detail="Repository not found")

        info = git_service.get_repo_info(config.src_dir, repo_name)
        readme_name, readme_html = markdown_service.find_repo_readme(config.src_dir / repo_name)

        return {
            "name": info.name,
            "path": info.path,
            "current_branch": info.current_branch,
            "default_branch": info.default_branch,
            "branches": info.branches,
            "remote_url": info.remote_url,
            "last_commits": [
                {"sha": c.sha, "message": c.message, "author": c.author, "date": c.date}
                for c in info.last_commits
            ],
            "readme_file": readme_name,
            "readme_html": readme_html,
        }

    async def get_repo_prs(repo_name: str):
        _validate_repo_name(repo_name)
        repos = git_service.discover_repos(config.src_dir)
        if repo_name not in repos:
            raise HTTPException(status_code=404, detail="Repository not found")
        info = git_service.get_repo_info(config.src_dir, repo_name)
        prs = github_service.get_open_prs(info.remote_url)
        return {
            "pull_requests": [
                {"number": pr.number, "title": pr.title, "author": pr.author,
                 "url": pr.url, "state": pr.state, "created_at": pr.created_at}
                for pr in prs
            ]
        }

    @app.get("/api/docs/tree")
    async def docs_tree():
        trees = markdown_service.build_md_tree(config.md_dirs)
        return {"trees": trees}

    @app.get("/api/docs/render")
    async def render_doc(path: str = Query(...)):
        html = markdown_service.render_md_file(path, config.md_dirs)
        if html is None:
            raise HTTPException(status_code=404, detail="File not found or not allowed")
        return {"html": html, "path": path, "name": Path(path).name}

    return app
