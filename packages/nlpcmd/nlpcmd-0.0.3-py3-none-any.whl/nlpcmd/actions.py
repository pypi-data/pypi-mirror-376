# Implementation of small actions. Keep safe and Windows-friendly.
import subprocess
import socket
import getpass
import platform
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple


def _is_virtual_adapter(name: str) -> bool:
    if not name:
        return False
    name = name.lower()
    virtual_tokens = ["virtual", "vmnet", "virtualbox", "docker", "vethernet", "hyper-v", "nat", "loopback", "host-only"]
    return any(tok in name for tok in virtual_tokens)


def show_ip(params: Dict[str, Any]) -> str:
    """
    Return IPv4 addresses. Uses socket method for a likely primary IP,
    parses `ipconfig` on Windows for all IPv4 addresses, deduplicates,
    and prefers a non-virtual adapter as primary.
    """
    sys_name = platform.system().lower()
    ips: List[Tuple[str, str]] = []  # list of (adapter_name, ip)

    # 1) try socket-based local IP (likely primary)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Using a public DNS address to pick the active interface; no packets are actually sent.
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and not primary_ip.startswith("127."):
            ips.append(("Local IP", primary_ip))
    except Exception:
        primary_ip = None

    # 2) On Windows, parse ipconfig output for IPv4 lines and adapter headers
    if sys_name == "windows":
        try:
            out = subprocess.check_output(["ipconfig"], universal_newlines=True, stderr=subprocess.DEVNULL)
            lines = out.splitlines()
            current_adapter = ""
            for line in lines:
                # Adapter header lines often end with "adapter <Name>:"
                adapter_m = re.match(r"^\s*([^\r\n].*Adapter.*):\s*$", line, re.I)
                if adapter_m:
                    current_adapter = adapter_m.group(1).strip()
                    continue
                ip_m = re.search(r"IPv4.*:\s*([\d\.]+)", line)
                if ip_m:
                    ip = ip_m.group(1).strip()
                    ips.append((current_adapter or "Adapter", ip))
        except Exception:
            # ignore parsing errors and continue with whatever we have
            pass
    else:
        # Non-Windows: try `ip` or `ifconfig` as a best-effort fallback (optional)
        try:
            # try `ip -4 addr` first (Linux)
            out = subprocess.check_output(["ip", "-4", "addr"], universal_newlines=True, stderr=subprocess.DEVNULL)
            # capture lines with "inet 192.168.x.x/..."
            for line in out.splitlines():
                m = re.search(r"inet\s+([\d\.]+)/\d+", line)
                if m:
                    ips.append(("iface", m.group(1)))
        except Exception:
            try:
                out = subprocess.check_output(["ifconfig"], universal_newlines=True, stderr=subprocess.DEVNULL)
                for line in out.splitlines():
                    m = re.search(r"inet\s+([\d\.]+)\s", line)
                    if m and not line.strip().startswith("127."):
                        ips.append(("iface", m.group(1)))
            except Exception:
                pass

    # 3) Dedupe and filter loopback; prefer non-virtual adapters for primary
    seen = set()
    cleaned: List[Tuple[str, str]] = []
    for name, ip in ips:
        if not ip or ip.startswith("127."):
            continue
        if ip in seen:
            continue
        seen.add(ip)
        cleaned.append((name or "Adapter", ip))

    if not cleaned:
        return "Could not determine IP address."

    # prefer first non-virtual adapter as primary
    primary = None
    for name, ip in cleaned:
        if not _is_virtual_adapter(name):
            primary = (name, ip)
            break
    if primary is None:
        primary = cleaned[0]

    result_lines = [f"Primary: {primary[1]} ({primary[0]})"]
    # list all unique addresses
    for name, ip in cleaned:
        result_lines.append(f"{name}: {ip}")
    return "\n".join(result_lines)


def whoami(params: Dict[str, Any]) -> str:
    return f"User: {getpass.getuser()} (platform: {platform.platform()})"


def greet(params: Dict[str, Any]) -> str:
    name = params.get("name") or "there"
    return f"Hello, {name}!"


def datetime_action(params: Dict[str, Any]) -> str:
    now = datetime.now()
    return now.strftime("Current time: %Y-%m-%d %H:%M:%S")


def ping_host(params: Dict[str, Any]) -> str:
    host = params.get("host")
    if not host:
        return "No host provided."
    # Use system ping; limit to 1 attempt for speed and safety.
    try:
        count_flag = "-n" if platform.system().lower().startswith("win") else "-c"
        out = subprocess.check_output(["ping", count_flag, "1", host], universal_newlines=True, stderr=subprocess.STDOUT, timeout=5)
        return f"Ping OK:\n{out}"
    except subprocess.CalledProcessError as e:
        return f"Ping failed:\n{e.output}"
    except Exception as e:
        return f"Ping error: {e}"


def unknown(params: Dict[str, Any]) -> str:
    return "Sorry — I didn't understand. Try: 'what is my ip', 'whoami', 'date', 'ping example.com', or 'say hello to Avik'."
