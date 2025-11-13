"""
Network discovery utilities to find hosts with SSH (port 22) open on local networks.

This module avoids external dependencies and is cross-platform. It attempts to
detect local IPv4 networks and scans them concurrently, providing callbacks for
progress, logs, and found hosts.
"""

import ipaddress
import platform
import socket
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, List, Optional, Tuple
import json
import time


def _run_command(command: List[str]) -> str:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    except Exception:
        return ""


def _parse_windows_ipconfig(output: str) -> List[Tuple[str, str]]:
    networks: List[Tuple[str, str]] = []
    current_ip: Optional[str] = None
    current_mask: Optional[str] = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("IPv4 Address") or line.startswith("IPv4 Address."):
            # e.g., "IPv4 Address. . . . . . . . . . . : 192.168.1.100"
            parts = line.split(":", 1)
            if len(parts) == 2:
                current_ip = parts[1].strip()
        elif line.startswith("Subnet Mask"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                current_mask = parts[1].strip()
        elif line.startswith("Default Gateway"):
            # boundary between interfaces; flush if we have both
            if current_ip and current_mask:
                networks.append((current_ip, current_mask))
            current_ip, current_mask = None, None
    # flush last
    if current_ip and current_mask:
        networks.append((current_ip, current_mask))
    return networks


def _parse_ip_addr(output: str) -> List[str]:
    # Parses `ip -o -4 addr show` lines like: "2: eth0    inet 192.168.1.42/24 brd 192.168.1.255 scope global ..."
    cidrs: List[str] = []
    for raw_line in output.splitlines():
        parts = raw_line.split()
        if "inet" in parts:
            try:
                idx = parts.index("inet")
                cidr = parts[idx + 1]
                # skip loopback
                if cidr.startswith("127."):
                    continue
                cidrs.append(cidr)
            except Exception:
                continue
    return cidrs


def detect_local_networks() -> List[ipaddress.IPv4Network]:
    """Detect local IPv4 networks on the current machine.

    Returns a list of IPv4Network objects (strict=False), deduplicated.
    """
    system = platform.system().lower()
    networks: List[ipaddress.IPv4Network] = []

    if "windows" in system:
        output = _run_command(["ipconfig"])
        pairs = _parse_windows_ipconfig(output)
        for ip_str, mask_str in pairs:
            try:
                net = ipaddress.IPv4Network((ip_str, mask_str), strict=False)
                if not net.is_loopback:
                    networks.append(net)
            except Exception:
                continue
    else:
        # Prefer `ip` if available
        output = _run_command(["ip", "-o", "-4", "addr", "show"]) or ""
        cidrs = _parse_ip_addr(output)
        if not cidrs:
            # Fallback to ifconfig
            output = _run_command(["ifconfig"]) or ""
            # naive parse: find lines with 'inet ' x.x.x.x and 'netmask' or 'mask'
            ip_str: Optional[str] = None
            mask_str: Optional[str] = None
            for raw in output.splitlines():
                line = raw.strip()
                if not line:
                    continue
                if line.startswith("inet ") and "127.0.0.1" not in line:
                    try:
                        ip_str = line.split()[1]
                    except Exception:
                        ip_str = None
                if "netmask" in line:
                    try:
                        # BSD/macOS shows hex mask sometimes; ipaddress accepts dotted only
                        mask_token = line.split("netmask", 1)[1].strip().split()[0]
                        if mask_token.startswith("0x"):
                            # convert hex like 0xffffff00 to dotted
                            mask_int = int(mask_token, 16)
                            mask_str = socket.inet_ntoa(mask_int.to_bytes(4, "big"))
                        else:
                            mask_str = mask_token
                    except Exception:
                        mask_str = None
                elif "Mask:" in line:
                    try:
                        mask_str = line.split("Mask:", 1)[1].strip().split()[0]
                    except Exception:
                        mask_str = None
                if ip_str and mask_str:
                    try:
                        net = ipaddress.IPv4Network((ip_str, mask_str), strict=False)
                        if not net.is_loopback:
                            networks.append(net)
                    except Exception:
                        pass
                    ip_str, mask_str = None, None
        else:
            for cidr in cidrs:
                try:
                    net = ipaddress.IPv4Network(cidr, strict=False)
                    if not net.is_loopback:
                        networks.append(net)
                except Exception:
                    continue

    # dedupe
    unique = []
    seen = set()
    for net in networks:
        if net.network_address.exploded + "/" + str(net.prefixlen) not in seen:
            unique.append(net)
            seen.add(net.network_address.exploded + "/" + str(net.prefixlen))
    return unique


def _try_connect(host: str, port: int, timeout: float) -> Tuple[bool, Optional[str]]:
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            try:
                # SSH servers usually send a banner immediately
                banner = sock.recv(256)
                banner_text = banner.decode("utf-8", errors="ignore").strip()
            except Exception:
                banner_text = None
            return True, banner_text
    except Exception:
        return False, None


def scan_network(
    network: ipaddress.IPv4Network,
    port: int = 22,
    timeout: float = 0.5,
    max_workers: int = 256,
    cancel_event: Optional[threading.Event] = None,
    on_log: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
    on_found: Optional[Callable[[str, Optional[str]], None]] = None,
) -> List[Tuple[str, Optional[str]]]:
    """Scan the given IPv4Network for open TCP port and report via callbacks.

    Returns a list of (host, banner) for hosts with the port open.
    """
    hosts: List[str] = [str(ip) for ip in network.hosts()]
    total = len(hosts)
    results: List[Tuple[str, Optional[str]]] = []

    if on_log:
        on_log(f"Starting scan {network.network_address}/{network.prefixlen} - {total} hosts")

    completed = 0

    def log(msg: str) -> None:
        if on_log:
            on_log(msg)

    if cancel_event is None:
        cancel_event = threading.Event()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_host = {
            executor.submit(_try_connect, host, port, timeout): host for host in hosts
        }
        for future in as_completed(future_to_host):
            if cancel_event.is_set():
                log("Scan cancelled")
                break
            host = future_to_host[future]
            ok = False
            banner = None
            try:
                ok, banner = future.result()
            except Exception:
                ok = False
            completed += 1
            if ok:
                results.append((host, banner))
                if on_found:
                    on_found(host, banner)
                log(f"OPEN {host}: {('SSH banner ' + banner) if banner else 'port 22 open'}")
            if on_progress:
                on_progress(completed, total)

    if on_log:
        log(f"Scan complete. Found {len(results)} host(s) with port {port} open.")
    return results


def discover_all_local(
    port: int = 22,
    timeout: float = 0.5,
    max_workers: int = 256,
    cancel_event: Optional[threading.Event] = None,
    on_log: Optional[Callable[[str], None]] = None,
    on_progress: Optional[Callable[[str, int, int], None]] = None,
    on_found: Optional[Callable[[str, str, Optional[str]], None]] = None,
) -> List[Tuple[str, str, Optional[str]]]:
    """Discover SSH hosts across all detected local networks.

    Returns a list of (network_cidr, host, banner).
    """
    networks = detect_local_networks()
    results: List[Tuple[str, str, Optional[str]]] = []
    if not networks:
        if on_log:
            on_log("No local IPv4 networks detected. Enter a subnet manually.")
        return results

    for net in networks:
        cidr = f"{net.network_address}/{net.prefixlen}"
        if on_log:
            on_log(f"\n=== Scanning network {cidr} ===")

        def per_net_progress(done: int, total: int) -> None:
            if on_progress:
                on_progress(cidr, done, total)

        def per_net_found(host: str, banner: Optional[str]) -> None:
            results.append((cidr, host, banner))
            if on_found:
                on_found(cidr, host, banner)

        scan_network(
            net,
            port=port,
            timeout=timeout,
            max_workers=max_workers,
            cancel_event=cancel_event,
            on_log=on_log,
            on_progress=per_net_progress,
            on_found=per_net_found,
        )

    if on_log:
        on_log(f"\nDiscovery complete across {len(networks)} network(s). Found {len(results)} host(s).")
    return results


# ------------------------
# UDP Beacon Discovery
# ------------------------

BEACON_PORT = 54545
BEACON_MAGIC = "swiftssh_beacon_v1"


def get_primary_ipv4() -> Optional[str]:
    try:
        # Does not send packets; used to determine outbound interface IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return None


def build_beacon_payload(ssh_port: int = 22) -> bytes:
    payload = {
        "magic": BEACON_MAGIC,
        "hostname": socket.gethostname(),
        "ip": get_primary_ipv4(),
        "ssh_port": ssh_port,
        "ts": int(time.time()),
    }
    return json.dumps(payload).encode("utf-8")


def listen_for_beacons(
    port: int = BEACON_PORT,
    on_log: Optional[Callable[[str], None]] = None,
    on_found: Optional[Callable[[str, str, int], None]] = None,
    stop_event: Optional[threading.Event] = None,
    timeout_s: Optional[float] = None,
) -> List[Tuple[str, str, int]]:
    """Listen for UDP beacon broadcasts and report hosts.

    Returns a list of (ip, hostname, ssh_port).
    """
    if stop_event is None:
        stop_event = threading.Event()
    discovered: List[Tuple[str, str, int]] = []
    seen = set()
    started_at = time.time()

    if on_log:
        on_log(f"Listening for beacons on UDP {port}...")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except Exception as e:
            if on_log:
                on_log(f"Failed to bind UDP {port}: {e}")
            return discovered
        sock.settimeout(0.5)

        while not stop_event.is_set():
            if timeout_s is not None and (time.time() - started_at) >= timeout_s:
                break
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except Exception as e:
                if on_log:
                    on_log(f"Listener error: {e}")
                continue
            try:
                payload = json.loads(data.decode("utf-8", errors="ignore"))
                if payload.get("magic") != BEACON_MAGIC:
                    continue
                ip = payload.get("ip") or addr[0]
                hostname = payload.get("hostname") or addr[0]
                ssh_port = int(payload.get("ssh_port") or 22)
            except Exception:
                continue

            key = (ip, hostname, ssh_port)
            if key in seen:
                continue
            seen.add(key)
            discovered.append((ip, hostname, ssh_port))
            if on_found:
                on_found(ip, hostname, ssh_port)
            if on_log:
                on_log(f"BEACON from {hostname} @ {ip}:{ssh_port}")

    if on_log:
        on_log(f"Beacon listening stopped. {len(discovered)} host(s) discovered.")
    return discovered


