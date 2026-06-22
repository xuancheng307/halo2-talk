#!/usr/bin/env python3
"""Local authoring server for the Halo2 deck.

Serves index.html + assets over http://localhost so the in-page edit/mark/delete
controls can auto-save to a file that Claude reads directly (no copy-paste).

  python authoring_server.py          # http://localhost:8000
  python authoring_server.py 8123     # custom port

Edits made in the browser are written to `.overrides.json` in this folder.
This server is for LOCAL AUTHORING ONLY — it is not used by the public site
(GitHub Pages) or the offline USB build, which fall back to localStorage.
"""
import http.server, socketserver, json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
OVF = os.path.join(DIR, ".overrides.json")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DIR, **k)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/load":
            data = b"{}"
            if os.path.exists(OVF):
                with open(OVF, "rb") as f:
                    data = f.read() or b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors(); self.end_headers()
            self.wfile.write(data)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] == "/save":
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            try:
                json.loads(body)  # validate it's JSON before writing
                with open(OVF, "wb") as f:
                    f.write(body)
                code = 200
            except Exception:
                code = 400
            self.send_response(code); self._cors(); self.end_headers()
            self.wfile.write(b"ok" if code == 200 else b"bad")
            return
        self.send_response(404); self._cors(); self.end_headers()

    def log_message(self, *a):
        pass  # quiet


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print("Halo2 authoring server: http://localhost:%d/index.html" % PORT)
        print("Edits auto-save to: %s" % OVF)
        httpd.serve_forever()
