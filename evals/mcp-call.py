#!/usr/bin/env python3
"""evals/mcp-call.py — minimal stdio JSON-RPC driver for the eval harness.

NOT part of the skill. This lets eval agents talk to the two MCP servers
through the shell in environments where the client has no MCP registration.
Read the safety notes in evals/README.md before using.

Usage:
  python3 evals/mcp-call.py mcp-cura <tool> ['<json-args>']
  python3 evals/mcp-call.py mcp-moonraker <tool> ['<json-args>']

Environment: MOONRAKER_URL is honored by mcp-moonraker as usual. For eval
runs set MOONRAKER_URL=http://127.0.0.1:9 so no real printer can be touched.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time

PROTOCOL_VERSION = "2025-11-25"
TIMEOUT_SECS = 60


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    binary, tool = sys.argv[1], sys.argv[2]
    args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                    "clientInfo": {"name": "eval-mcp-call", "version": "0.1.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": tool, "arguments": args}},
    ]

    proc = subprocess.Popen([binary], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, text=True, bufsize=1)
    out_lines: list[str] = []
    stop = threading.Event()

    def reader():
        for line in proc.stdout:
            if stop.is_set():
                break
            out_lines.append(line)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    try:
        for req in requests:
            proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()

        deadline = time.time() + TIMEOUT_SECS
        while time.time() < deadline:
            for line in list(out_lines):
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if msg.get("id") == 2:
                    stop.set()
                    proc.terminate()
                    result = msg.get("result", msg.get("error", {}))
                    print(json.dumps(result, indent=2))
                    return 0
            time.sleep(0.05)

        stop.set()
        proc.terminate()
        sys.exit(f"timeout after {TIMEOUT_SECS}s waiting for {binary}")
    finally:
        stop.set()
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
