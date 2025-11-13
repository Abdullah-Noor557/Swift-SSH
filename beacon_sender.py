"""
SwiftSSH Beacon Sender

Run this script on another PC to broadcast its hostname and IP address over the
local network so the SwiftSSH app can discover it instantly.

Usage:
    python beacon_sender.py [--port 22] [--interval 2.0] [--udp 54545]
"""

import argparse
import socket
import sys
import time
from typing import List
from core.network_discovery import build_beacon_payload, BEACON_PORT


def get_broadcast_addresses() -> List[str]:
    # Send to 255.255.255.255 by default; optionally include common subnets
    return ["255.255.255.255"]


def main() -> int:
    parser = argparse.ArgumentParser(description="SwiftSSH Beacon Sender")
    parser.add_argument("--port", type=int, default=22, help="SSH port to advertise")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between beacons")
    parser.add_argument("--udp", type=int, default=BEACON_PORT, help="UDP port to broadcast on")
    args = parser.parse_args()

    payload = build_beacon_payload(ssh_port=args.port)
    addrs = get_broadcast_addresses()

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                for addr in addrs:
                    try:
                        sock.sendto(payload, (addr, args.udp))
                    except Exception:
                        pass
                time.sleep(args.interval)
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Beacon sender error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())


