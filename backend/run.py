"""Entry point used by the desktop app (and the bundled binary).

    python run.py --data-dir ~/Atelier --port 8765
"""

import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Atelier backend")
    parser.add_argument("--data-dir", help="Library folder (overrides ATELIER_DATA_DIR)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--server-url", help="Store imports on this Atelier server (e.g. the NAS)"
    )
    args = parser.parse_args()

    if args.data_dir:
        os.environ["ATELIER_DATA_DIR"] = args.data_dir
    if args.server_url:
        os.environ["ATELIER_SERVER_URL"] = args.server_url

    # Settings are read at import time, so import the app after setting env.
    import uvicorn
    from main import app

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
