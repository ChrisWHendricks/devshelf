from pathlib import Path
from dataclasses import dataclass, field

import yaml


@dataclass
class Config:
    src_dir: Path = Path.home() / "src"
    md_dirs: list[Path] = field(default_factory=lambda: [Path.home() / "docs"])
    host: str = "127.0.0.1"
    port: int = 8400

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text()) or {}
        return cls(
            src_dir=Path(raw.get("src_dir", "~/src")).expanduser(),
            md_dirs=[Path(d).expanduser() for d in raw.get("md_dirs", ["~/docs"])],
            host=raw.get("host", "127.0.0.1"),
            port=raw.get("port", 8400),
        )

    def override(self, src_dir: str | None, md_dirs: list[str] | None, host: str | None, port: int | None) -> "Config":
        if src_dir:
            self.src_dir = Path(src_dir).expanduser()
        if md_dirs:
            self.md_dirs = [Path(d).expanduser() for d in md_dirs]
        if host:
            self.host = host
        if port:
            self.port = port
        return self
