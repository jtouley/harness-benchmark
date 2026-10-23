"""Relay one TCP port on the trial network's gateway to the host's HTTPS proxy.

    python3 runner/proxy_relay.py --listen 172.17.0.1:3129 --upstream 127.0.0.1:41549
    python3 runner/proxy_relay.py --host-ports 172.17.0.1 --except 3129

A host whose outbound traffic must go through a local proxy (`HTTPS_PROXY=http://127.0.0.1:PORT`) cannot
give that address to a container: 127.0.0.1 in the container is the container. run_trial.sh --auth proxy
starts this relay on the gateway of the Docker bridge, and the trial gets
`HTTPS_PROXY=http://<gateway>:<port>`. The relay copies bytes and reads none: the proxy sees the
container's CONNECT requests as its own. It prints one line when it listens and never logs traffic.

`--host-ports GATEWAY` prints the TCP ports the host listens on that a container on the bridge could
open (bound to any address, or to the gateway's), less `--except`: run_trial.sh probes each one.
"""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import struct
import sys


def _addr(text: str) -> tuple[str, int]:
    host, _, port = text.rpartition(":")
    if not host or not port.isdigit():
        raise argparse.ArgumentTypeError(f"not HOST:PORT: {text}")
    return host, int(port)


def host_ports(gateway: str, tables: tuple[str, ...] = ("/proc/net/tcp", "/proc/net/tcp6")) -> set[int]:
    """Listening TCP ports bound to the unspecified address or to `gateway` (also as an IPv4-mapped one)."""
    ports = set()
    for name in tables:
        try:
            lines = open(name, encoding="ascii").read().splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            if len(fields) < 4 or fields[3] != "0A":  # 0A: LISTEN
                continue
            addr_hex, port_hex = fields[1].split(":")
            raw = bytes.fromhex(addr_hex)  # 32-bit words in host (little-endian) order
            addr = ipaddress.ip_address(b"".join(struct.pack(">I", w)
                                                 for w in struct.unpack(f"<{len(raw) // 4}I", raw)))
            mapped = getattr(addr, "ipv4_mapped", None)
            if addr.is_unspecified or str(addr) == gateway or (mapped is not None and str(mapped) == gateway):
                ports.add(int(port_hex, 16))
    return ports


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        writer.close()


async def _serve(listen: tuple[str, int], upstream: tuple[str, int]) -> None:
    async def handle(c_reader: asyncio.StreamReader, c_writer: asyncio.StreamWriter) -> None:
        try:
            u_reader, u_writer = await asyncio.open_connection(*upstream)
        except OSError:
            c_writer.close()
            return
        await asyncio.gather(_pipe(c_reader, u_writer), _pipe(u_reader, c_writer))

    server = await asyncio.start_server(handle, *listen)
    print(f"proxy_relay: listening on {listen[0]}:{listen[1]}", flush=True)
    async with server:
        await server.serve_forever()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--listen", type=_addr)
    ap.add_argument("--upstream", type=_addr)
    ap.add_argument("--host-ports", metavar="GATEWAY")
    ap.add_argument("--except", dest="skip", type=int, action="append", default=[])
    args = ap.parse_args(argv)
    if args.host_ports:
        print(" ".join(str(p) for p in sorted(host_ports(args.host_ports) - set(args.skip))))
        return 0
    if not (args.listen and args.upstream):
        ap.error("--listen and --upstream are required")
    try:
        asyncio.run(_serve(args.listen, args.upstream))
    except OSError as e:
        print(f"proxy_relay: cannot listen on {args.listen[0]}:{args.listen[1]}: {e.strerror}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
