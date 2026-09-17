"""Small CONNECT-only allowlisting proxy; deploy on two Docker networks.

The client network is internal. Only this proxy gets a public network attachment.
No TLS interception, credentials, DNS aliases or arbitrary forward HTTP requests.
"""
from __future__ import annotations

import ipaddress
import os
import select
import socket
import socketserver


def allowed_host(host: str, patterns: list[str]) -> bool:
    host = host.lower().rstrip(".")
    return any(host == p.lower() or (p.startswith("*.") and host.endswith(p[1:].lower())
                                   and host != p[2:].lower()) for p in patterns)


def public_addresses(host: str, port: int):
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not infos or any(not ipaddress.ip_address(info[4][0]).is_global for info in infos):
        raise ValueError("destination resolves to a non-public address")
    return infos


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(20)
        line = self.rfile.readline(8193)
        if len(line) > 8192:
            return
        try:
            method, authority, _ = line.decode("ascii").split()
            host, port_text = authority.rsplit(":", 1)
            port = int(port_text)
            if method != "CONNECT" or port != 443 or not allowed_host(host, self.server.patterns):
                raise ValueError("not allowed")
            total = 0
            while True:
                header = self.rfile.readline(8193)
                total += len(header)
                if total > 32768 or not header:
                    raise ValueError("invalid headers")
                if header in (b"\r\n", b"\n"):
                    break
            infos = public_addresses(host, port)
            upstream = None
            for family, kind, proto, _, address in infos:
                sock = socket.socket(family, kind, proto)
                sock.settimeout(20)
                try:
                    sock.connect(address)
                    upstream = sock
                    break
                except OSError:
                    sock.close()
            if upstream is None:
                raise OSError("upstream unavailable")
        except (ValueError, UnicodeError, OSError):
            self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n")
            return
        self.wfile.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        self.wfile.flush()
        self.connection.settimeout(None)
        upstream.settimeout(None)
        try:
            sockets = [self.connection, upstream]
            while True:
                readable, _, _ = select.select(sockets, [], [], 600)
                if not readable:
                    break
                for src in readable:
                    data = src.recv(65536)
                    if not data:
                        return
                    (upstream if src is self.connection else self.connection).sendall(data)
        except OSError:
            pass
        finally:
            upstream.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("0.0.0.0", 8080), Handler) as server:
        server.patterns = os.environ["ALLOWED_HOSTS"].split(",")
        server.serve_forever()
