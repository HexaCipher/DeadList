"""
DeadList Diff Engine
Compares pslist vs psscan outputs to detect DKOM-hidden processes.

The core insight: pslist walks the EPROCESS linked list (same as Task Manager),
while psscan does a raw memory scan. A rootkit can unlink from pslist but
can't hide from psscan's brute-force scan. Any PID in psscan but NOT in
pslist is a DKOM-hidden process.
"""

from typing import Dict, List, Set, Any


def compare_processes(
    pslist_output: List[Dict[str, Any]],
    psscan_output: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare pslist and psscan outputs to find hidden and anomalous processes.

    Args:
        pslist_output: List of process dicts from windows.pslist
        psscan_output: List of process dicts from windows.psscan

    Returns:
        Dict with hidden_pids, anomalous_pids, and merged process list
    """
    # Extract PID sets from both sources
    pslist_pids: Set[int] = set()
    psscan_pids: Set[int] = set()

    pslist_map: Dict[int, Dict[str, Any]] = {}
    psscan_map: Dict[int, Dict[str, Any]] = {}

    for proc in pslist_output:
        pid = proc.get("PID", proc.get("pid", 0))
        if pid:
            pslist_pids.add(pid)
            pslist_map[pid] = proc

    for proc in psscan_output:
        pid = proc.get("PID", proc.get("pid", 0))
        if pid:
            psscan_pids.add(pid)
            psscan_map[pid] = proc

    # Core diff logic
    # Hidden: in psscan but NOT in pslist → DKOM rootkit behavior
    hidden_pids = psscan_pids - pslist_pids

    # Anomalous: in pslist but NOT in psscan → rare anomaly
    anomalous_pids = pslist_pids - psscan_pids

    # Normal: in both lists
    normal_pids = pslist_pids & psscan_pids

    # Build merged process list with status annotations
    merged_processes = []

    # Hidden processes first (highest priority)
    for pid in sorted(hidden_pids):
        proc = psscan_map[pid]
        merged_processes.append({
            "pid": pid,
            "ppid": proc.get("PPID", proc.get("ppid")),
            "name": proc.get("ImageFileName", proc.get("name", "Unknown")),
            "in_pslist": False,
            "in_psscan": True,
            "is_hidden": True,
            "status": "hidden",
            "create_time": proc.get("CreateTime", proc.get("create_time")),
            "offset": proc.get("Offset", proc.get("offset")),
        })

    # Anomalous processes
    for pid in sorted(anomalous_pids):
        proc = pslist_map[pid]
        merged_processes.append({
            "pid": pid,
            "ppid": proc.get("PPID", proc.get("ppid")),
            "name": proc.get("ImageFileName", proc.get("name", "Unknown")),
            "in_pslist": True,
            "in_psscan": False,
            "is_hidden": False,
            "status": "anomalous",
            "create_time": proc.get("CreateTime", proc.get("create_time")),
            "offset": proc.get("Offset", proc.get("offset")),
        })

    # Normal processes
    for pid in sorted(normal_pids):
        # Prefer pslist data for normal processes
        proc = pslist_map[pid]
        merged_processes.append({
            "pid": pid,
            "ppid": proc.get("PPID", proc.get("ppid")),
            "name": proc.get("ImageFileName", proc.get("name", "Unknown")),
            "in_pslist": True,
            "in_psscan": True,
            "is_hidden": False,
            "status": "clean",
            "create_time": proc.get("CreateTime", proc.get("create_time")),
            "offset": proc.get("Offset", proc.get("offset")),
        })

    return {
        "hidden_pids": sorted(list(hidden_pids)),
        "anomalous_pids": sorted(list(anomalous_pids)),
        "normal_pids": sorted(list(normal_pids)),
        "hidden_count": len(hidden_pids),
        "anomalous_count": len(anomalous_pids),
        "total_count": len(merged_processes),
        "merged_processes": merged_processes,
    }
