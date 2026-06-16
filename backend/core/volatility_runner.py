"""
DeadList Volatility Runner
Runs Volatility 3 plugins via subprocess and parses JSON output.
Includes mock mode for development without real memory dumps.

Volatility 3 JSON output format:
{
    "columns": ["PID", "PPID", "ImageFileName", ...],
    "data": [
        {"PID": 4, "PPID": 0, "ImageFileName": "System", ...},
        ...
    ]
}
"""

import json
import subprocess
import asyncio
import logging
import random
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config import settings

logger = logging.getLogger(__name__)

PLUGINS = [
    "windows.pslist",
    "windows.psscan",
    "windows.netscan",
    "windows.malfind",
    "windows.cmdline",
]


def _find_volatility_binary() -> str:
    """
    Locate the Volatility 3 binary.
    Checks the configured path first, then common install locations.
    """
    # 1. Check configured path
    if shutil.which(settings.VOLATILITY_PATH):
        return settings.VOLATILITY_PATH

    # 2. Check common locations
    common_paths = [
        "vol",
        "vol3",
        "volatility3",
        "python -m volatility3.cli",
    ]
    for path in common_paths:
        if shutil.which(path.split()[0]):
            return path

    # 3. Check pip-installed location (works in Docker)
    vol_path = shutil.which("vol")
    if vol_path:
        return vol_path

    raise FileNotFoundError(
        "Volatility 3 not found. Install it with: pip install volatility3 "
        "or set VOLATILITY_PATH in .env"
    )


def _parse_vol3_json(raw_output: str, plugin_name: str) -> List[Dict[str, Any]]:
    """
    Parse Volatility 3's JSON renderer output into a list of dicts.

    Volatility 3 can output in two formats:
    1. Array of objects (newer versions / some plugins)
    2. {"columns": [...], "data": [...]} (older format)

    We handle both gracefully.
    """
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed for {plugin_name}: {e}")
        logger.debug(f"Raw output (first 500 chars): {raw_output[:500]}")
        raise RuntimeError(f"Failed to parse {plugin_name} JSON output: {e}")

    # Format 1: Already a list of dicts
    if isinstance(parsed, list):
        return parsed

    # Format 2: {"columns": [...], "data": [...]}
    if isinstance(parsed, dict):
        # Some versions wrap in a top-level key
        if "data" in parsed:
            data = parsed["data"]
            columns = parsed.get("columns", [])

            # If data items are lists (not dicts), zip with columns
            if data and isinstance(data[0], list) and columns:
                return [dict(zip(columns, row)) for row in data]

            # If data items are already dicts
            if data and isinstance(data[0], dict):
                return data

            return data if isinstance(data, list) else []

        # Some plugins return a single dict with results
        return [parsed]

    return []


async def run_plugin(
    dump_path: str,
    plugin_name: str,
    timeout: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Run a single Volatility 3 plugin against a memory dump.

    Args:
        dump_path: Path to the memory dump file
        plugin_name: Volatility plugin name (e.g. 'windows.pslist')
        timeout: Per-plugin timeout in seconds

    Returns:
        List of result dicts parsed from Volatility's JSON output
    """
    if settings.MOCK_MODE:
        return await _run_mock_plugin(plugin_name)

    timeout = timeout or settings.PLUGIN_TIMEOUT_SECONDS

    # Find the Volatility binary
    vol_binary = _find_volatility_binary()

    # Build the command
    # Volatility 3 CLI: vol -f <dump> -r json <plugin>
    cmd = [
        vol_binary,
        "-f", dump_path,
        "-r", "json",
        plugin_name,
    ]

    logger.info(f"Running Volatility: {' '.join(cmd)}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )

        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        # Log warnings from stderr (Volatility prints progress info there)
        if stderr_text:
            for line in stderr_text.split("\n"):
                if "error" in line.lower() or "exception" in line.lower():
                    logger.warning(f"[{plugin_name}] stderr: {line}")
                else:
                    logger.debug(f"[{plugin_name}] stderr: {line}")

        if process.returncode != 0:
            logger.error(f"Plugin {plugin_name} failed (exit code {process.returncode}): {stderr_text}")
            raise RuntimeError(
                f"Plugin {plugin_name} failed (exit code {process.returncode}): {stderr_text[:500]}"
            )

        output = stdout.decode("utf-8", errors="replace").strip()

        if not output:
            logger.warning(f"Plugin {plugin_name} returned empty output")
            return []

        results = _parse_vol3_json(output, plugin_name)
        logger.info(f"Plugin {plugin_name} returned {len(results)} results")
        return results

    except asyncio.TimeoutError:
        logger.error(f"Plugin {plugin_name} timed out after {timeout}s")
        # Try to kill the hung process
        try:
            process.kill()
        except Exception:
            pass
        raise TimeoutError(f"Plugin {plugin_name} timed out after {timeout}s")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {plugin_name} output: {e}")
        raise RuntimeError(f"Failed to parse {plugin_name} output: {e}")


# ─── Mock Data Generators ────────────────────────────────────

# Realistic Windows process set for mock data
MOCK_SYSTEM_PROCESSES = [
    {"pid": 0, "ppid": 0, "name": "Idle", "cmdline": ""},
    {"pid": 4, "ppid": 0, "name": "System", "cmdline": ""},
    {"pid": 88, "ppid": 4, "name": "Registry", "cmdline": ""},
    {"pid": 340, "ppid": 4, "name": "smss.exe", "cmdline": r"\SystemRoot\System32\smss.exe"},
    {"pid": 444, "ppid": 340, "name": "csrss.exe", "cmdline": r"%SystemRoot%\system32\csrss.exe ObjectDirectory=\Windows SharedSection=1024,20480,768"},
    {"pid": 520, "ppid": 340, "name": "wininit.exe", "cmdline": "wininit.exe"},
    {"pid": 528, "ppid": 512, "name": "csrss.exe", "cmdline": r"%SystemRoot%\system32\csrss.exe ObjectDirectory=\Windows SharedSection=1024,20480,768"},
    {"pid": 612, "ppid": 520, "name": "services.exe", "cmdline": r"C:\Windows\system32\services.exe"},
    {"pid": 620, "ppid": 520, "name": "lsass.exe", "cmdline": r"C:\Windows\system32\lsass.exe"},
    {"pid": 708, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\system32\svchost.exe -k DcomLaunch -p"},
    {"pid": 756, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\system32\svchost.exe -k RPCSS -p"},
    {"pid": 884, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\System32\svchost.exe -k LocalServiceNetworkRestricted -p"},
    {"pid": 948, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\system32\svchost.exe -k netsvcs -p"},
    {"pid": 1024, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\System32\svchost.exe -k LocalSystemNetworkRestricted -p"},
    {"pid": 1116, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\System32\svchost.exe -k LocalServiceNoNetwork -p"},
    {"pid": 1264, "ppid": 612, "name": "spoolsv.exe", "cmdline": r"C:\Windows\System32\spoolsv.exe"},
    {"pid": 1456, "ppid": 948, "name": "taskhostw.exe", "cmdline": "taskhostw.exe"},
    {"pid": 1788, "ppid": 1780, "name": "explorer.exe", "cmdline": r"C:\Windows\Explorer.EXE"},
    {"pid": 2104, "ppid": 1788, "name": "chrome.exe", "cmdline": r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'},
    {"pid": 2340, "ppid": 2104, "name": "chrome.exe", "cmdline": r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --type=renderer'},
    {"pid": 2456, "ppid": 1788, "name": "notepad.exe", "cmdline": r'"C:\Windows\system32\notepad.exe"'},
    {"pid": 3012, "ppid": 612, "name": "svchost.exe", "cmdline": r"C:\Windows\system32\svchost.exe -k UnistackSvcGroup"},
    {"pid": 3144, "ppid": 612, "name": "SecurityHealthService.exe", "cmdline": r"C:\Windows\system32\SecurityHealthService.exe"},
]

# Malicious processes only in psscan (DKOM-hidden)
MOCK_HIDDEN_PROCESSES = [
    {"pid": 6664, "ppid": 612, "name": "svch0st.exe", "cmdline": ""},
    {"pid": 7788, "ppid": 6664, "name": "payload.exe", "cmdline": r"C:\Users\victim\AppData\Local\Temp\payload.exe -connect 185.141.27.98:4444"},
]

MOCK_NETWORK_CONNECTIONS = [
    {"pid": 948, "protocol": "TCPv4", "local_addr": "0.0.0.0", "local_port": 135, "remote_addr": "0.0.0.0", "remote_port": 0, "state": "LISTENING"},
    {"pid": 2104, "protocol": "TCPv4", "local_addr": "192.168.1.105", "local_port": 49234, "remote_addr": "142.250.190.78", "remote_port": 443, "state": "ESTABLISHED"},
    {"pid": 2104, "protocol": "TCPv4", "local_addr": "192.168.1.105", "local_port": 49240, "remote_addr": "172.217.14.99", "remote_port": 443, "state": "ESTABLISHED"},
    {"pid": 2340, "protocol": "TCPv4", "local_addr": "192.168.1.105", "local_port": 49250, "remote_addr": "151.101.1.140", "remote_port": 443, "state": "ESTABLISHED"},
    {"pid": 708, "protocol": "TCPv4", "local_addr": "0.0.0.0", "local_port": 445, "remote_addr": "0.0.0.0", "remote_port": 0, "state": "LISTENING"},
    {"pid": 620, "protocol": "TCPv4", "local_addr": "0.0.0.0", "local_port": 49664, "remote_addr": "0.0.0.0", "remote_port": 0, "state": "LISTENING"},
    # Malicious connections
    {"pid": 7788, "protocol": "TCPv4", "local_addr": "192.168.1.105", "local_port": 49890, "remote_addr": "185.141.27.98", "remote_port": 4444, "state": "ESTABLISHED"},
    {"pid": 6664, "protocol": "TCPv4", "local_addr": "192.168.1.105", "local_port": 49891, "remote_addr": "91.215.85.142", "remote_port": 8888, "state": "ESTABLISHED"},
    {"pid": 6664, "protocol": "TCPv4", "local_addr": "0.0.0.0", "local_port": 1337, "remote_addr": "0.0.0.0", "remote_port": 0, "state": "LISTENING"},
]

MOCK_MALFIND_RESULTS = [
    {
        "pid": 6664,
        "process_name": "svch0st.exe",
        "address": "0x00400000",
        "size": 4096,
        "protection": "PAGE_EXECUTE_READWRITE",
        "hex_dump": "4D 5A 90 00 03 00 00 00 04 00 00 00 FF FF 00 00\nB8 00 00 00 00 00 00 00 40 00 00 00 00 00 00 00\n00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
        "disassembly": "0x00400000: dec ebp\n0x00400001: pop edx\n0x00400002: nop\n0x00400003: add [ebx], al",
        "tag": "MZ Header - Injected PE",
    },
    {
        "pid": 7788,
        "process_name": "payload.exe",
        "address": "0x10000000",
        "size": 8192,
        "protection": "PAGE_EXECUTE_READWRITE",
        "hex_dump": "FC E8 82 00 00 00 60 89 E5 31 C0 64 8B 50 30 8B\n52 0C 8B 52 14 8B 72 28 0F B7 4A 26 31 FF AC 3C\n61 7C 02 2C 20 C1 CF 0D 01 C7 E2 F2 52 57 8B 52",
        "disassembly": "0x10000000: cld\n0x10000001: call 0x10000086\n0x10000006: pushad\n0x10000007: mov ebp, esp",
        "tag": "Shellcode - Metasploit Stager",
    },
    {
        "pid": 1788,
        "process_name": "explorer.exe",
        "address": "0x20000000",
        "size": 2048,
        "protection": "PAGE_EXECUTE_READWRITE",
        "hex_dump": "55 8B EC 83 EC 10 53 56 57 8B 7D 08 8B F1 85 FF\n74 05 83 3F 00 75 1E 68 00 10 00 00 6A 00 FF 15",
        "disassembly": "0x20000000: push ebp\n0x20000001: mov ebp, esp\n0x20000003: sub esp, 0x10",
        "tag": "Suspicious RWX Region",
    },
]


async def _run_mock_plugin(plugin_name: str) -> List[Dict[str, Any]]:
    """Generate realistic mock data for development without Volatility."""
    # Simulate processing time (0.5-3 seconds per plugin)
    await asyncio.sleep(random.uniform(0.5, 3.0))

    if plugin_name == "windows.pslist":
        # pslist sees normal processes ONLY (not hidden ones)
        return [
            {
                "PID": p["pid"],
                "PPID": p["ppid"],
                "ImageFileName": p["name"],
                "CreateTime": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "Offset": hex(random.randint(0x80000000, 0xFFFFFFFF)),
            }
            for p in MOCK_SYSTEM_PROCESSES
        ]

    elif plugin_name == "windows.psscan":
        # psscan sees ALL processes including hidden ones
        all_procs = MOCK_SYSTEM_PROCESSES + MOCK_HIDDEN_PROCESSES
        return [
            {
                "PID": p["pid"],
                "PPID": p["ppid"],
                "ImageFileName": p["name"],
                "CreateTime": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "Offset": hex(random.randint(0x80000000, 0xFFFFFFFF)),
            }
            for p in all_procs
        ]

    elif plugin_name == "windows.netscan":
        return [
            {
                "PID": c["pid"],
                "Proto": c["protocol"],
                "LocalAddr": c["local_addr"],
                "LocalPort": c["local_port"],
                "ForeignAddr": c["remote_addr"],
                "ForeignPort": c["remote_port"],
                "State": c["state"],
            }
            for c in MOCK_NETWORK_CONNECTIONS
        ]

    elif plugin_name == "windows.malfind":
        return [
            {
                "PID": m["pid"],
                "Process": m["process_name"],
                "Address": m["address"],
                "Size": m["size"],
                "Protection": m["protection"],
                "Hexdump": m["hex_dump"],
                "Disasm": m["disassembly"],
                "Tag": m["tag"],
            }
            for m in MOCK_MALFIND_RESULTS
        ]

    elif plugin_name == "windows.cmdline":
        all_procs = MOCK_SYSTEM_PROCESSES + MOCK_HIDDEN_PROCESSES
        return [
            {
                "PID": p["pid"],
                "Process": p["name"],
                "Args": p["cmdline"],
            }
            for p in all_procs
        ]

    return []


def check_volatility_available() -> dict:
    """
    Check if Volatility 3 is available on the system.
    Returns a dict with status info.
    """
    if settings.MOCK_MODE:
        return {
            "available": False,
            "mode": "mock",
            "message": "Running in mock mode — Volatility 3 not required",
        }

    try:
        vol_binary = _find_volatility_binary()
        result = subprocess.run(
            [vol_binary, "--help"],
            capture_output=True, timeout=10,
        )
        return {
            "available": result.returncode == 0,
            "mode": "live",
            "binary": vol_binary,
            "message": "Volatility 3 is ready",
        }
    except FileNotFoundError:
        return {
            "available": False,
            "mode": "live",
            "message": "Volatility 3 not found — install it or set MOCK_MODE=True",
        }
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "mode": "live",
            "message": "Volatility 3 check timed out",
        }
