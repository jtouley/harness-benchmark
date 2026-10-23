"""runner/proxy_relay.py: the relay from the Docker bridge's gateway to the host's proxy, and the list of
host ports a container on the bridge could open."""
from __future__ import annotations

import importlib.util
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELAY = ROOT / "runner" / "proxy_relay.py"
_spec = importlib.util.spec_from_file_location("proxy_relay", RELAY)
proxy_relay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(proxy_relay)

# /proc/net/tcp rows: 0.0.0.0:2024 and 172.17.0.1:5000 and 127.0.0.1:41549 listening (0A), 0.0.0.0:22
# connected (01). Addresses are 32-bit words in little-endian order.
TCP = """  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode
   0: 00000000:07E8 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 1
   1: 010011AC:1388 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 2
   2: 0100007F:A245 00000000:0000 0A 00000000:00000000 00:00000000 00000000     0        0 3
   3: 00000000:0016 0100007F:9C40 01 00000000:00000000 00:00000000 00000000     0        0 4
"""
# /proc/net/tcp6: [::]:8080 and [::ffff:172.17.0.1]:6000 listening, [::1]:7000 listening.
TCP6 = """  sl  local_address                         remote_address                        st
   0: 00000000000000000000000000000000:1F90 00000000000000000000000000000000:0000 0A
   1: 0000000000000000FFFF0000010011AC:1770 00000000000000000000000000000000:0000 0A
   2: 00000000000000000000000001000000:1B58 00000000000000000000000000000000:0000 0A
"""


def test_host_ports_lists_what_a_container_on_the_bridge_could_open(tmp_path):
    (tmp_path / "tcp").write_text(TCP)
    (tmp_path / "tcp6").write_text(TCP6)
    ports = proxy_relay.host_ports("172.17.0.1", (str(tmp_path / "tcp"), str(tmp_path / "tcp6")))
    # Not 41549 (loopback only), 22 (not listening) or 7000 (::1).
    assert ports == {2024, 5000, 8080, 6000}


def test_relay_copies_bytes_both_ways():
    upstream = socket.socket()
    upstream.bind(("127.0.0.1", 0))
    upstream.listen()

    def echo() -> None:
        conn, _ = upstream.accept()
        with conn:
            while data := conn.recv(1024):
                conn.sendall(data.upper())

    threading.Thread(target=echo, daemon=True).start()
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    relay = subprocess.Popen([sys.executable, str(RELAY), "--listen", f"127.0.0.1:{port}",
                              "--upstream", f"127.0.0.1:{upstream.getsockname()[1]}"],
                             stdout=subprocess.PIPE, text=True)
    try:
        assert relay.stdout.readline().startswith("proxy_relay: listening on 127.0.0.1:")
        with socket.create_connection(("127.0.0.1", port), timeout=5) as c:
            c.sendall(b"connect example:443\n")
            deadline, got = time.time() + 5, b""
            while len(got) < 20 and time.time() < deadline:
                got += c.recv(1024)
        assert got == b"CONNECT EXAMPLE:443\n"
    finally:
        relay.terminate()
        relay.wait(5)
        upstream.close()


def test_relay_needs_both_addresses():
    r = subprocess.run([sys.executable, str(RELAY), "--listen", "127.0.0.1:1"], capture_output=True, text=True)
    assert r.returncode == 2 and "--listen and --upstream are required" in r.stderr
