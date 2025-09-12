import os
import re
import ssl
import time
import socket
import threading
import traceback
from datetime import datetime, timezone
from typing import Callable, Dict, Optional
from pathlib import Path

# ------------------------
# Helpers
# ------------------------

def rfc1123_date(ts: Optional[float] = None) -> str:
    dt = datetime.fromtimestamp(ts if ts is not None else time.time(), tz=timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def ensure_self_signed_certificate(cert_path: str, key_path: str):
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    if os.path.exists(cert_path) and os.path.exists(key_path):
        return
    log("Generating self-signed certificate...")

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"AU"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"GurtServer"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(int(time.time()))
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow().replace(year=datetime.now(timezone.utc).year + 1))
        .sign(key, hashes.SHA256())
    )

    with open(key_path, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    log("Certificate generated.")

def build_tls_context(cert_file: str, key_file: str) -> ssl.SSLContext:
    ensure_self_signed_certificate(cert_file, key_file)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    try:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    except AttributeError:
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    try:
        ctx.set_alpn_protocols(["GURT/1.0"])
    except Exception:
        pass
    return ctx

def read_until_double_crlf(sock: socket.socket, max_bytes=64 * 1024) -> bytes:
    data = b""
    while b"\r\n\r\n" not in data and len(data) < max_bytes:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data

def parse_headers(raw: bytes):
    try:
        head, _ = raw.split(b"\r\n\r\n", 1)
    except ValueError:
        head = raw
    return [line.decode("utf-8", errors="replace") for line in head.split(b"\r\n")]

def http_status_message(code: int) -> str:
    return {
        200: "OK",
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        500: "INTERNAL_SERVER_ERROR",
    }.get(code, "UNKNOWN")

def send_gurt_response(tls_conn: ssl.SSLSocket, status: int, content_type: str, body: str):
    status_message = http_status_message(status)
    body_bytes = body.encode("utf-8", errors="replace")
    headers = [
        f"GURT/1.0.0 {status} {status_message}",
        f"date: {rfc1123_date()}",
        "server: jasperGURT/1.0.0",
        f"content-type: {content_type}",
        f"content-length: {len(body_bytes)}",
        "",
        "",
    ]
    tls_conn.sendall("\r\n".join(headers).encode("utf-8"))
    if body_bytes:
        tls_conn.sendall(body_bytes)

def send_gurt_error(conn, status: int, message: str):
    body = f"<h1>{status}</h1><p>{message}</p>"
    try:
        send_gurt_response(conn, status, "text/html; charset=utf-8", body)
    except Exception:
        try:
            conn.sendall(body.encode("utf-8"))
        except Exception:
            pass

# ------------------------r
# Main app class
# ------------------------
class Gurt:
    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.cert_file = "certs/cert.pem"
        self.key_file = "certs/key.pem"
        self.views_dir = "src/views"
        self.layouts_dir = "src/layouts"
        self.tls_ctx = build_tls_context(self.cert_file, self.key_file)

    def route(self, path: str):
        regex_pattern = re.sub(r'<([^>]+)>', r'(?P<\1>[^/]+)', path)
        regex_pattern = f"^{regex_pattern}$"

        def decorator(func: Callable):
            self.routes[re.compile(regex_pattern)] = func
            return func
        return decorator

    def init(self, host="0.0.0.0", port=4878):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(50)
        log(f"GURT app running on gurt://{host}:{port}")
        try:
            while True:
                conn, addr = sock.accept()
                threading.Thread(
                    target=self.handle_client, args=(conn, addr), daemon=True
                ).start()
        except KeyboardInterrupt:
            log("Shutting down...")
        finally:
            sock.close()

    def handle_client(self, conn: socket.socket, address):
        peer = f"{address[0]}:{address[1]}"
        try:
            # --- Handshake ---
            raw = read_until_double_crlf(conn)
            if not raw:
                conn.close()
                return
            lines = parse_headers(raw)
            if not lines or not lines[0].upper().startswith("HANDSHAKE"):
                conn.close()
                return
            hs_resp = (
                "GURT/1.0.0 101 SWITCHING_PROTOCOLS\r\n"
                "gurt-version: 1.0.0\r\n"
                "encryption: TLS/1.3\r\n"
                "alpn: GURT/1.0\r\n"
                "server: py-gurt-gateway/0.1\r\n"
                f"date: {rfc1123_date()}\r\n"
                "\r\n"
            ).encode("utf-8")
            conn.sendall(hs_resp)

            # --- Upgrade to TLS ---
            try:
                tls_conn = self.tls_ctx.wrap_socket(conn, server_side=True)
            except ssl.SSLError as e:
                log(f"[{peer}] TLS upgrade failed: {e}")
                conn.close()
                return

            # --- Read request ---
            raw_req = read_until_double_crlf(tls_conn)
            if not raw_req:
                tls_conn.close()
                return
            req_lines = parse_headers(raw_req)
            if not req_lines:
                send_gurt_error(tls_conn, 400, "Bad Request: empty")
                tls_conn.close()
                return
            parts = req_lines[0].split()
            if len(parts) != 3:
                send_gurt_error(tls_conn, 400, "Bad Request: malformed")
                tls_conn.close()
                return
            method, path, _ = parts
            if method.upper() != "GET":
                send_gurt_error(tls_conn, 405, "Method Not Allowed")
                tls_conn.close()
                return

            # --- Route dispatch ---
            matched_handler = None
            path_params = {}

            # Iterate through routes to find a matching regex
            for pattern, handler in self.routes.items():
                match = pattern.match(path)
                if match:
                    matched_handler = handler
                    path_params = match.groupdict()
                    break
            
            if matched_handler:
                try:
                    response = matched_handler(**path_params)
                    
                    if not isinstance(response, dict):
                        send_gurt_error(tls_conn, 500, f"A dictionary wasn't returned by the route {path}")
                        tls_conn.close()
                        return
                    
                    body = response.get("body", "")
                    content_type = response.get("content_type", "text/html")

                    send_gurt_response(tls_conn, 200, content_type, body)
                except Exception as e:
                    traceback.print_exc()
                    send_gurt_error(tls_conn, 500, "Internal Server Error")
            elif Path("static", path.split("/", 1)[1]).exists():
                file = Path("static", path.split("/", 1)[1])
                with open(file, "r") as f:
                    body = f.read()
                send_gurt_response(tls_conn, 200, "text/plain", body)
            else:
                send_gurt_error(tls_conn, 404, "Not Found")

            tls_conn.close()
        except Exception as e:
            log(f"[{peer}] Exception: {e}\n{traceback.format_exc()}")
            try:
                send_gurt_error(conn, 500, "Internal Server Error")
            except Exception:
                pass
            conn.close()

    def render(self, filePath: str, **vars) -> dict:
        layout_path = Path(self.layouts_dir, "main.gurt")
        if not layout_path.exists():
            raise FileNotFoundError(f"Layout file not found: {layout_path}")

        view_content = self.render_file(filePath, **vars)["body"]
        
        with open(layout_path, "r") as f:
            layout_content = f.read()

        final_content = layout_content.replace("{{{ body }}}", view_content)

        for key, value in vars.items():
            placeholder = f"{{{{ {key} }}}}"
            final_content = final_content.replace(placeholder, str(value))
        
        return {
            "body": final_content,
            "content_type": "text/html; charset=utf-8"
        }

    def render_file(self, filePath: str, **vars) -> dict:
        view_path = Path(self.views_dir, filePath)
        if not view_path.exists():
            raise FileNotFoundError(f"View file not found: {view_path}")

        with open(view_path, "r") as f:
            content = f.read()

        for key, value in vars.items():
            placeholder = f"{{{{ {key} }}}}"
            content = content.replace(placeholder, str(value))

        return {
            "body": content,
            "content_type": "text/html; charset=utf-8"
        }