from __future__ import annotations

import hashlib
import json
import os
import threading
import mimetypes
import time
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask.typing import ResponseReturnValue
from platformdirs import user_cache_dir
from pathspec import PathSpec


PKG_NAME = "codecam"
MAX_MB = int(os.getenv("CODECAM_MAX_MB", "2"))
IDLE_TIMEOUT_SECONDS = int(os.getenv("CODECAM_IDLE", "60"))


def _cache_file_for(cwd: str) -> Path:
    """Return a per-project cache file path for selected files, keyed by CWD hash."""
    p = Path(cwd).resolve()
    h = hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:16]
    cache_dir = Path(user_cache_dir(PKG_NAME))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"selected_files_{h}.json"


def _normalize_for_web(path: str) -> str:
    """Return a POSIX-style path for sending to the browser (stable across OSes)."""
    return Path(path).as_posix()


def _openable_local_path(path: str) -> Path:
    """
    Convert a POSIX string from the browser back into a local filesystem path.
    Works on all OSes.
    """
    return Path(path)


def _load_gitignore(root: Path) -> PathSpec | None:
    gi = root / ".gitignore"
    if not gi.exists():
        return None
    return PathSpec.from_lines("gitwildmatch", gi.read_text().splitlines())


def _is_probably_text(p: Path) -> bool:
    mt, _ = mimetypes.guess_type(p.name)
    if mt is None:
        return True
    return mt.startswith("text/") or mt in {"application/json", "application/xml"}


def create_app(default_path: str = ".") -> Flask:
    """
    Create the Flask app.
    - Caches selection per working directory
    - Provides /browse, /generate, /shutdown
    - Includes an idle reaper thread to exit when idle
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")
    project_root = Path(default_path).resolve()
    gitignore = _load_gitignore(project_root)

    # ---- idle reaper state
    last_seen = {"ts": time.time()}

    def _bump_idle() -> None:
        last_seen["ts"] = time.time()

    @app.before_request  # type: ignore[misc]
    def _before_request() -> None:
        _bump_idle()

    def _reaper() -> None:
        # Daemon thread that kills the process when no requests for a while.
        while True:
            time.sleep(2)
            if time.time() - last_seen["ts"] > IDLE_TIMEOUT_SECONDS:
                os._exit(0)

    threading.Thread(target=_reaper, daemon=True).start()
    # ----

    @app.route("/")  # type: ignore[misc]
    def index() -> ResponseReturnValue:
        selected_path = _cache_file_for(default_path)
        selected_files: list[str]
        if selected_path.exists():
            try:
                selected_files = json.loads(selected_path.read_text())
            except Exception:
                selected_files = []
        else:
            selected_files = []

        current_directory = str(Path(default_path).resolve())
        return render_template(
            "index.html",
            default_path=default_path,
            selected_files=selected_files,
            current_directory=current_directory,
        )

    @app.route("/browse", methods=["POST"])  # type: ignore[misc]
    def browse() -> ResponseReturnValue:
        payload = request.get_json(silent=True) or {}
        # normalize: blank -> project root
        project_root = Path(default_path).resolve()
        root_path = Path(payload.get("path") or project_root).resolve()

        files: list[str] = []
        try:
            for root, dirs, filenames in os.walk(str(root_path)):
                root_abs = Path(root).resolve()

                # prune noise dirs
                dirs[:] = [
                    d
                    for d in dirs
                    if d
                    not in ("venv", "__pycache__", ".mypy_cache", ".ruff_cache", ".git")
                ]

                # apply .gitignore to dirs (relative to project_root)
                if gitignore:
                    kept = []
                    for d in dirs:
                        p = (root_abs / d).resolve()
                        try:
                            rel = p.relative_to(project_root)
                        except ValueError:
                            # outside project root -> drop
                            continue
                        if not gitignore.match_file(rel.as_posix()):
                            kept.append(d)
                    dirs[:] = kept

                # files
                for filename in filenames:
                    p = (root_abs / filename).resolve()
                    try:
                        rel = p.relative_to(project_root)
                    except ValueError:
                        # outside project root
                        continue
                    if gitignore and gitignore.match_file(rel.as_posix()):
                        continue
                    files.append(rel.as_posix())
        except Exception as e:
            print("browser error:", e)
            files = []

        return jsonify(files=files)

    @app.route("/generate", methods=["POST"])  # type: ignore[misc]
    def generate() -> ResponseReturnValue:
        payload = request.get_json(silent=True) or {}
        files = payload.get("files", [])
        result = _generate_snapshot(files)
        # Persist selection for this working dir
        _cache_file_for(default_path).write_text(json.dumps(files))
        return jsonify(result=result)

    @app.route("/shutdown", methods=["POST"])  # type: ignore[misc]
    def shutdown() -> ResponseReturnValue:
        # Graceful stop for werkzeug dev server; fallback to hard exit
        func = request.environ.get("werkzeug.server.shutdown")
        if func is None:
            os._exit(0)
        func()
        return "Server shutting down..."

    def _generate_snapshot(files: list[str] | None) -> str | None:
        if files is None:
            sel = _cache_file_for(default_path)
            if not sel.exists():
                return None
            files = json.loads(sel.read_text())

        import platform
        from datetime import datetime

        header = (
            f"System: {platform.system()} {platform.release()} {platform.version()}\n"
            f"Time: {datetime.now()}\n"
        )
        chunks: list[str] = [header]

        project_root = Path(default_path).resolve()

        for f in files:
            p = Path(f)
            if not p.is_absolute():  # resolve relative to project root
                p = (project_root / p).resolve()
            try:
                p.relative_to(project_root)  # confine to root
            except ValueError:
                continue
            if p.is_symlink() or p.is_dir():
                continue
            try:
                if p.stat().st_size > MAX_MB * 1024 * 1024:
                    content = f"<<SKIPPED: {p.name} larger than {MAX_MB} MB>>"
                elif not _is_probably_text(p):
                    content = f"<<SKIPPED: {p.name} appears binary (not text/*)>>"
                else:
                    content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                content = f"<<ERROR READING FILE: {e}>>"

            # Use a relative header for neat output
            rel = p.relative_to(project_root).as_posix()
            chunks.append(f"--- {rel} ---\n{content}\n")

        return "".join(chunks)

    return app
