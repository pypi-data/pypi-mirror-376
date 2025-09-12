from __future__ import annotations

import argparse
import os
import platform
import webbrowser

from . import __version__
from .web import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codecam", description="Share code selections with an LLM"
    )
    parser.add_argument(
        "path", nargs="?", default=".", help="Project path (default: .)"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--port", type=int, default=0, help="0 chooses a random free port"
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return

    app = create_app(args.path)

    # pick free port if 0
    import socket

    if args.port == 0:
        with socket.socket() as s:
            s.bind((args.host, 0))
            args.port = s.getsockname()[1]

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        if platform.system() == "Linux" and "Microsoft" in platform.uname().release:
            os.system(f"powershell.exe Start-Process {url}")  # WSL case
        else:
            webbrowser.open(url)

    # threaded True to ensure shutdown handler doesn't deadlock
    app.run(host=args.host, port=args.port, threaded=True, use_reloader=False)
