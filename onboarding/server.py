"""Local intake API. It does not run the prepared-example crew."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

from onboarding.demo_guard import enabled, token_ok
from onboarding.router import health, read_hire, submit_event
from onboarding.store import DEFAULT_DB_PATH, CaseStore


HOST = "127.0.0.1"
PORT = 8000
MAX_BODY = 65536
WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/src/main.js": "src/main.js",
}
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


def load_runtime_env() -> None:
    """Load the repository-root .env. Variables already set stay as they are."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def main() -> int:
    load_runtime_env()
    host, port = listen_address()
    store = CaseStore(database_path())
    server = ThreadingHTTPServer((host, port), _handler(store))
    print(f"Listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
        store.close()
    return 0


def _handler(store: CaseStore):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/health":
                status, body = health(store)
                shown = dict(body)
                shown["demo_lock"] = enabled()
                _send(self, status, shown)
                return
            prefix = "/hires/"
            if path.startswith(prefix):
                hire_id = unquote(path[len(prefix) :])
                if hire_id and "/" not in hire_id:
                    status, body = read_hire(store, hire_id)
                    _send(self, status, body)
                    return
            if _send_static(self, path):
                return
            _send(self, 404, {"message": "That address is not part of this increment."})

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            _cors(self)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Demo-Token")
            self.end_headers()

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path != "/events":
                _send(self, 404, {"message": "That address is not part of this increment."})
                return
            if not token_ok(self.headers.get("X-Demo-Token")):
                _send(
                    self,
                    401,
                    {
                        "code": "demo_lock",
                        "message": "This demonstration requires the access token. No case was changed.",
                    },
                )
                return
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
            except ValueError:
                length = -1
            if length < 0 or length > MAX_BODY:
                _send(
                    self,
                    400,
                    {
                        "code": "unreadable_input",
                        "message": "The intake could not be read, so no plan was written.",
                    },
                )
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                _send(
                    self,
                    400,
                    {
                        "code": "unreadable_input",
                        "message": "The intake could not be read, so no plan was written.",
                    },
                )
                return
            try:
                status, body = submit_event(store, payload)
            except Exception as exc:
                print(f"Event failed ({type(exc).__name__}).", flush=True)
                _send(self, 500, {"message": "The case could not be saved."})
                return
            _send(self, status, body)

        def log_message(self, fmt: str, *args) -> None:
            print("%s %s" % (self.address_string(), fmt % args), flush=True)

    return Handler


def _send(handler: BaseHTTPRequestHandler, status: int, body: dict) -> None:
    encoded = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    _cors(handler)
    handler.end_headers()
    handler.wfile.write(encoded)


def _send_static(handler: BaseHTTPRequestHandler, path: str) -> bool:
    name = STATIC_FILES.get(path)
    if name is None:
        return False
    file_path = WORKSPACE / name
    if not file_path.is_file():
        return False
    encoded = file_path.read_bytes()
    suffix = file_path.suffix
    handler.send_response(200)
    handler.send_header("Content-Type", CONTENT_TYPES.get(suffix, "application/octet-stream"))
    handler.send_header("Content-Length", str(len(encoded)))
    _cors(handler)
    handler.end_headers()
    handler.wfile.write(encoded)
    return True


def _cors(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")


def listen_address() -> tuple[str, int]:
    host = os.environ.get("ONBOARDING_HOST", HOST).strip() or HOST
    raw_port = os.environ.get("PORT", str(PORT)).strip() or str(PORT)
    return host, int(raw_port)


def database_path() -> Path:
    raw = os.environ.get("ONBOARDING_DB_PATH", "").strip()
    return Path(raw) if raw else DEFAULT_DB_PATH


if __name__ == "__main__":
    raise SystemExit(main())
