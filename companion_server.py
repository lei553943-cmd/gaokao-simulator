"""Minimal companion: serves HTML + proxies to Ollama. No config needed."""
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error

HTML_FILE = Path(__file__).parent / "xb.html"
OLLAMA = "http://127.0.0.1:11434/v1/chat/completions"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            html = HTML_FILE.read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                data["model"] = "qwen2.5:3b"
                data["stream"] = False
                req_body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                req = urllib.request.Request(
                    OLLAMA, data=req_body,
                    headers={"Content-Type": "application/json; charset=utf-8"},
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(result)
            except Exception as e:
                print(f"ERROR: {e}, body[:100]={body[:100]!r}")
                self.send_response(502)
                self.end_headers()
                err = str(e).encode("ascii", errors="replace").decode("ascii")
                resp = json.dumps({"reply": f"连接失败: {err}", "status": "error"}, ensure_ascii=False)
                self.wfile.write(resp.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        print(f"[{args[0]}] {args[1]} {args[2]}")  # minimal log

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8765), Handler)
    print("小伴已启动: http://127.0.0.1:8765")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
