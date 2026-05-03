"""确保 SQLite 父目录存在。"""
from pathlib import Path

def ensure_sqlite_dirs(database_url: str) -> None:
    if not database_url.startswith("sqlite"):
        return
    # sqlite:///relative/path.db or sqlite:////abs/path.db
    rest = database_url[len("sqlite:") :]
    if rest.startswith("///") and not rest.startswith("////"):
        # three slashes: relative
        path_str = rest[3:]
    elif rest.startswith("////"):
        path_str = rest[4:]
    else:
        return
    if path_str.startswith(":memory") or "mode=memory" in path_str:
        return
    path = Path(path_str.split("?")[0])
    if path.parent and str(path.parent) != ".":
        path.parent.mkdir(parents=True, exist_ok=True)
