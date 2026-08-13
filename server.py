import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime, timezone

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("server.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

LOGIN_PATHS = ["/login", "/auth", "/api/login", "/api/auth"]


class GameAuthHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        # отключаем стандартный логгер http.server, чтобы не дублировать
        pass

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='replace')

        logger.info(
            f"[REQUEST] {self.client_address[0]} | POST {path} | "
            f"Content-Length: {content_length} | Body preview: {body[:512]}{'...' if len(body) > 512 else ''}"
        )

        if path in LOGIN_PATHS:
            logger.warning(
                f"[LOGIN REQUEST] {self.client_address[0]} | Path: {path} | Query: {query} | Full body: {body}"
            )

        response = {
            "status": "ok",
            "message": "Request received",
            "path": path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        logger.info(f"[REQUEST] {self.client_address[0]} | GET {path}")

        response = {
            "status": "ok",
            "message": "Server is running",
            "path": path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))


def run():
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8080))  # берём из Railway, иначе 8080
    server_address = (host, port)
    httpd = HTTPServer(server_address, GameAuthHandler)
    logger.info(f"Starting server on {host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    run()
