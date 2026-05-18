#!/usr/bin/env python3
"""Local demo server for static assets and embed token refresh."""

import argparse
import io
import json
import os
import sys
from contextlib import redirect_stdout
from datetime import timezone
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from embed_token import generate_embed_token, get_aad_token, load_config


ROOT = Path(__file__).resolve().parent.parent


def _to_unix_timestamp(dt):
    return int(dt.astimezone(timezone.utc).timestamp())


class DemoRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/favicon.ico"):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        if self.path.startswith("/api/embed-token"):
            self.handle_embed_token()
            return

        if self.path.startswith("/api/health"):
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def handle_embed_token(self):
        diagnostics = io.StringIO()
        try:
            with redirect_stdout(diagnostics):
                config = load_config()
                force_refresh = "refresh=1" in self.path.lower()
                aad_token = get_aad_token(config, force_refresh=force_refresh)
                embed_token, embed_expiry = generate_embed_token(
                    config,
                    aad_token,
                    force_refresh=force_refresh,
                )
            payload = {
                "token": embed_token,
                "tokenType": "embed",
                "expiresAt": embed_expiry.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "expiresAtUnix": _to_unix_timestamp(embed_expiry),
                "reportId": config["fabric"]["reportId"],
                "embedUrl": config["fabric"]["reportUrl"].replace(
                    "/groups/",
                    "/reportEmbed?groupId=",
                ).replace(
                    "/reports/",
                    "&reportId=",
                ),
                "workspaceId": config["fabric"]["workspaceId"],
            }
            self._send_json(HTTPStatus.OK, payload)
        except SystemExit as exc:
            printed_message = diagnostics.getvalue().strip()
            self._send_json(HTTPStatus.BAD_REQUEST, {
                "error": "configuration_error",
                "message": printed_message or str(exc) or "Token generation failed",
            })
        except Exception as exc:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {
                "error": "token_generation_failed",
                "message": str(exc),
            })


def main():
    parser = argparse.ArgumentParser(description="Run the local VISA demo server")
    parser.add_argument("--host", default=os.getenv("DEMO_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DEMO_PORT", "8000")))
    args = parser.parse_args()

    handler = partial(DemoRequestHandler, directory=str(ROOT))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving VISA demo from {ROOT}")
    print(f"Open http://{args.host}:{args.port}/pbi-app-injection-demo.html")
    print("Embed token endpoint: /api/embed-token")
    server.serve_forever()


if __name__ == "__main__":
    main()