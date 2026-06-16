"""
DeadList Scoring Engine
Assigns a suspicion score (0–100) to each process based on 7 forensic criteria.
"""

from typing import Dict, List, Any, Optional
import re


# Known malicious / suspicious ports commonly used by C2 frameworks
SUSPICIOUS_PORTS = {
    4444,   # Metasploit default
    1337,   # Common backdoor
    8888,   # Various malware
    5555,   # Android ADB, some C2s
    6666,   # Various backdoors
    6667,   # IRC (often C2 channel)
    31337,  # Back Orifice
    12345,  # NetBus
    54321,  # Back Orifice 2000
    1234,   # Common test/malware
    9999,   # Various
    7777,   # Various
    3333,   # Various miners
}

# Legitimate Windows system processes and their expected parents
SYSTEM_PROCESSES = {
    "system": {"expected_ppid": 0},
    "smss.exe": {"expected_ppid": 4},
    "csrss.exe": {"expected_ppid_name": "smss.exe"},
    "wininit.exe": {"expected_ppid_name": "smss.exe"},
    "winlogon.exe": {"expected_ppid_name": "smss.exe"},
    "services.exe": {"expected_ppid_name": "wininit.exe"},
    "lsass.exe": {"expected_ppid_name": "wininit.exe"},
    "svchost.exe": {"expected_ppid_name": "services.exe"},
    "explorer.exe": {"expected_ppid_name": "userinit.exe"},
}

# Common typosquatting variants of system processes
SYSTEM_PROCESS_NAMES = [
    "svchost.exe", "csrss.exe", "lsass.exe", "services.exe",
    "explorer.exe", "winlogon.exe", "smss.exe", "wininit.exe",
    "spoolsv.exe", "taskhost.exe", "conhost.exe",
]

# Suspicious parent-child relationships
SUSPICIOUS_PARENTS = {
    "cmd.exe": ["winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe", "iexplore.exe"],
    "powershell.exe": ["winword.exe", "excel.exe", "powerpnt.exe", "outlook.exe"],
    "wscript.exe": ["winword.exe", "excel.exe"],
    "cscript.exe": ["winword.exe", "excel.exe"],
    "mshta.exe": ["winword.exe", "excel.exe", "outlook.exe"],
    "regsvr32.exe": ["winword.exe", "excel.exe"],
}


def _is_typosquatting(name: str) -> bool:
    """Check if a process name is a typosquatting variant of a system process."""
    name_lower = name.lower()

    # Exact matches are fine
    if name_lower in [sp.lower() for sp in SYSTEM_PROCESS_NAMES]:
        return False

    # Check for similar names (edit distance 1-2)
    for sys_name in SYSTEM_PROCESS_NAMES:
        sys_lower = sys_name.lower()
        if name_lower == sys_lower:
            continue

        # Check letter substitution patterns (e.g., svch0st vs svchost)
        if len(name_lower) == len(sys_lower):
            diffs = sum(1 for a, b in zip(name_lower, sys_lower) if a != b)
            if diffs <= 2:
                return True

        # Check for extra/missing characters
        if abs(len(name_lower) - len(sys_lower)) == 1:
            longer = name_lower if len(name_lower) > len(sys_lower) else sys_lower
            shorter = sys_lower if len(name_lower) > len(sys_lower) else name_lower
            diffs = 0
            j = 0
            for i in range(len(longer)):
                if j < len(shorter) and longer[i] == shorter[j]:
                    j += 1
                else:
                    diffs += 1
            if diffs <= 1:
                return True

    return False


def _has_suspicious_parent(
    process_name: str,
    parent_name: Optional[str]
) -> bool:
    """Check if the parent-child relationship is suspicious (e.g., cmd from Word)."""
    if not parent_name:
        return False

    proc_lower = process_name.lower()
    parent_lower = parent_name.lower()

    for child, suspicious_parents in SUSPICIOUS_PARENTS.items():
        if proc_lower == child:
            if parent_lower in [p.lower() for p in suspicious_parents]:
                return True

    return False


def calculate_score(
    process: Dict[str, Any],
    connections: List[Dict[str, Any]],
    malfind_results: List[Dict[str, Any]],
    all_processes: Optional[Dict[int, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Calculate suspicion score for a single process.

    Args:
        process: Process dict with pid, name, ppid, is_hidden, cmdline, etc.
        connections: Network connections owned by this PID
        malfind_results: Malfind results for this PID
        all_processes: Map of all processes by PID (to resolve parent names)

    Returns:
        Dict with total_score, status, and breakdown list
    """
    score = 0
    breakdown = []
    pid = process.get("pid", 0)
    name = process.get("name", "Unknown")
    ppid = process.get("ppid")
    cmdline = process.get("cmdline")
    is_hidden = process.get("is_hidden", False)

    # Get parent process name if available
    parent_name = None
    if all_processes and ppid and ppid in all_processes:
        parent_name = all_processes[ppid].get("name")

    # ── Criterion 1: Hidden process (DKOM) ────────────────────
    if is_hidden:
        score += 50
        breakdown.append({
            "criterion": "Hidden Process (DKOM)",
            "points": 50,
            "severity": "CRITICAL",
            "description": f"PID {pid} found in psscan but NOT in pslist — classic DKOM rootkit behavior",
        })

    # ── Criterion 2: Suspicious parent-child relationship ─────
    if _has_suspicious_parent(name, parent_name):
        score += 25
        breakdown.append({
            "criterion": "Suspicious Parent Process",
            "points": 25,
            "severity": "HIGH",
            "description": f"{name} spawned by {parent_name} — possible macro malware or exploit",
        })

    # ── Criterion 3: Empty or null command line ───────────────
    if cmdline is None or cmdline.strip() == "":
        # Only flag if it's not a system process that normally has no cmdline
        if name.lower() not in ("system", "registry", "secure system", "idle"):
            score += 15
            breakdown.append({
                "criterion": "Empty Command Line",
                "points": 15,
                "severity": "MEDIUM",
                "description": "Process has no command line arguments — malware often omits or clears cmdline",
            })

    # ── Criterion 4: Known malicious port ─────────────────────
    suspicious_ports_found = []
    for conn in connections:
        local_port = conn.get("local_port", 0)
        remote_port = conn.get("remote_port", 0)
        if local_port in SUSPICIOUS_PORTS:
            suspicious_ports_found.append(f"local:{local_port}")
        if remote_port in SUSPICIOUS_PORTS:
            suspicious_ports_found.append(f"remote:{remote_port}")

    if suspicious_ports_found:
        score += 20
        breakdown.append({
            "criterion": "Known Malicious Port",
            "points": 20,
            "severity": "HIGH",
            "description": f"Connection on suspicious port(s): {', '.join(suspicious_ports_found)}",
        })

    # ── Criterion 5: Foreign/unusual IP connection ────────────
    unusual_ips = []
    for conn in connections:
        remote = conn.get("remote_addr", "")
        if remote and remote not in ("0.0.0.0", "127.0.0.1", "::", "::1", "*", ""):
            # Filter out private ranges
            if not (
                remote.startswith("10.") or
                remote.startswith("172.16.") or remote.startswith("172.17.") or
                remote.startswith("172.18.") or remote.startswith("172.19.") or
                remote.startswith("172.2") or remote.startswith("172.3") or
                remote.startswith("192.168.") or
                remote.startswith("169.254.") or
                remote.startswith("fe80:")
            ):
                unusual_ips.append(remote)

    if unusual_ips:
        score += 10
        breakdown.append({
            "criterion": "External IP Connection",
            "points": 10,
            "severity": "MEDIUM",
            "description": f"Connected to {len(unusual_ips)} external IP(s): {', '.join(unusual_ips[:3])}",
        })

    # ── Criterion 6: RWX memory region (malfind) ──────────────
    if malfind_results:
        score += 30
        breakdown.append({
            "criterion": "Injected Code (RWX Region)",
            "points": 30,
            "severity": "CRITICAL",
            "description": f"{len(malfind_results)} suspicious memory region(s) with executable permissions — possible shellcode or process hollowing",
        })

    # ── Criterion 7: Name mimicking system process ────────────
    if _is_typosquatting(name):
        score += 20
        breakdown.append({
            "criterion": "System Process Mimicry",
            "points": 20,
            "severity": "HIGH",
            "description": f"Process name '{name}' appears to mimic a legitimate Windows system process",
        })

    # Cap score at 100
    total_score = min(score, 100)

    # Determine status based on score
    if is_hidden:
        status = "hidden"
    elif total_score >= 50:
        status = "suspicious"
    elif total_score >= 20:
        status = "suspicious"
    else:
        status = "clean"

    return {
        "total_score": total_score,
        "status": status,
        "breakdown": breakdown,
    }


def determine_risk_level(
    hidden_count: int,
    max_score: int,
    suspicious_count: int
) -> str:
    """
    Determine overall risk level for the analysis.

    Args:
        hidden_count: Number of hidden processes
        max_score: Highest individual suspicion score
        suspicious_count: Number of processes with score >= 30

    Returns:
        Risk level string: clean/low/medium/high/critical
    """
    if hidden_count > 0 or max_score >= 80:
        return "critical"
    elif max_score >= 50 or suspicious_count >= 3:
        return "high"
    elif max_score >= 30 or suspicious_count >= 1:
        return "medium"
    elif max_score >= 10:
        return "low"
    else:
        return "clean"
