from pathlib import Path
from typing import Optional

import typer
import uvicorn

from .config import Config
from .main import create_app

app = typer.Typer(help="Code Registry - visualize local git repos and browse Markdown files")


@app.command()
def serve(
    src_dir: Optional[str] = typer.Option(None, "--dir", "-d", help="Parent directory to scan for git repos"),
    md_dirs: Optional[list[str]] = typer.Option(None, "--md-dir", "-m", help="Directory containing Markdown files (can specify multiple)"),
    host: Optional[str] = typer.Option(None, "--host", help="Host to bind to"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to bind to"),
    config_file: Path = typer.Option("config.yaml", "--config", "-c", help="Path to config file"),
):
    """Start the Code Registry web server."""
    cfg = Config.from_yaml(config_file)
    cfg.override(src_dir, md_dirs, host, port)

    typer.echo(f"Scanning repos in: {cfg.src_dir}")
    for d in cfg.md_dirs:
        typer.echo(f"Markdown dir: {d}")
    typer.echo(f"Starting server at http://{cfg.host}:{cfg.port}")

    fastapi_app = create_app(cfg)
    uvicorn.run(fastapi_app, host=cfg.host, port=cfg.port)


if __name__ == "__main__":
    app()
