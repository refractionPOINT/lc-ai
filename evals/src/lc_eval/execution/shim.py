#!/usr/bin/env python3
"""Candidate-side CLI transport. No LC credentials and no task-specific logic."""
import base64
import http.client
import json
import os
import socket
import sys


class UnixConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/run/lc-eval/broker.sock")


def main():
    conn = UnixConnection("localhost", timeout=650)
    data = sys.stdin.buffer.read(16_000_001) if not sys.stdin.isatty() else b""
    if len(data) > 16_000_000:
        print("CLI transport stdin limit exceeded", file=sys.stderr)
        return 125
    request = json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
                          "stdin": base64.b64encode(data).decode()}).encode()
    try:
        conn.request("POST", "/execute", body=request, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        if response.status != 200:
            response.read()
            print("CLI transport rejected request", file=sys.stderr)
            return 125
        code = 125
        while line := response.readline():
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise TypeError("event must be an object")
                event_type = event.get("type")
                if event_type in ("stdout", "stderr"):
                    payload = base64.b64decode(event["data"], validate=True)
                    stream = sys.stdout.buffer if event_type == "stdout" else sys.stderr.buffer
                    stream.write(payload)
                    stream.flush()
                elif event_type == "exit" and isinstance(event.get("code"), int):
                    code = event["code"]
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                print("CLI transport returned an invalid response", file=sys.stderr)
                return 125
        return code
    except (OSError, http.client.HTTPException):
        print("CLI transport unavailable", file=sys.stderr)
        return 125
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
