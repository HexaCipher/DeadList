"""
DeadList Analysis Pipeline
Orchestrates the full analysis flow: plugin execution → diff → scoring → save.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession

from core.volatility_runner import run_plugin, PLUGINS
from core.diff_engine import compare_processes
from core.scoring_engine import calculate_score, determine_risk_level, SUSPICIOUS_PORTS
from core.geoip import resolve_ips_batch
from config import settings
from models.database import Analysis, Process, NetworkConnection, MemoryRegion

logger = logging.getLogger(__name__)


async def run_analysis(
    analysis_id: str,
    dump_path: str,
    db: AsyncSession,
    ws_broadcast,
):
    """
    Run the full analysis pipeline for a memory dump.

    Steps:
        1. Set analysis status to 'running'
        2. Run 5 Volatility plugins in parallel
        3. Run diff engine (pslist vs psscan)
        4. Run scoring engine on all processes
        5. Resolve GeoIP for network connections
        6. Save everything to database
        7. Broadcast analysis_complete

    Args:
        analysis_id: UUID of the analysis
        dump_path: Path to the memory dump file
        db: Database session
        ws_broadcast: Async function to broadcast WebSocket events
    """
    try:
        # Step 1: Update status to running
        analysis = await db.get(Analysis, analysis_id)
        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return
        analysis.status = "running"
        await db.commit()

        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 5,
            "message": "Analysis started — preparing plugins...",
        })

        # Step 2: Run all 5 plugins concurrently
        plugin_results: Dict[str, List[Dict[str, Any]]] = {}
        plugin_tasks = {}

        for plugin in PLUGINS:
            await ws_broadcast(analysis_id, {
                "event": "plugin_started",
                "plugin": plugin,
                "timestamp": datetime.utcnow().isoformat(),
            })

        # Run all plugins concurrently
        tasks = {
            plugin: asyncio.create_task(run_plugin(dump_path, plugin))
            for plugin in PLUGINS
        }

        completed_count = 0
        for plugin, task in tasks.items():
            try:
                result = await task
                plugin_results[plugin] = result
                completed_count += 1

                await ws_broadcast(analysis_id, {
                    "event": "plugin_complete",
                    "plugin": plugin,
                    "timestamp": datetime.utcnow().isoformat(),
                    "count": len(result),
                })

                progress = 10 + (completed_count * 14)  # 10-80%
                await ws_broadcast(analysis_id, {
                    "event": "progress",
                    "percent": progress,
                    "message": f"✅ {plugin} complete — {len(result)} results found",
                })

            except Exception as e:
                logger.error(f"Plugin {plugin} failed: {e}")
                plugin_results[plugin] = []
                completed_count += 1

                await ws_broadcast(analysis_id, {
                    "event": "plugin_error",
                    "plugin": plugin,
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                })

        # Step 3: Run diff engine
        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 82,
            "message": "Running diff engine — comparing pslist vs psscan...",
        })

        pslist_output = plugin_results.get("windows.pslist", [])
        psscan_output = plugin_results.get("windows.psscan", [])
        diff_result = compare_processes(pslist_output, psscan_output)

        # Broadcast hidden process alerts
        for pid in diff_result["hidden_pids"]:
            hidden_proc = next(
                (p for p in diff_result["merged_processes"] if p["pid"] == pid),
                None,
            )
            if hidden_proc:
                await ws_broadcast(analysis_id, {
                    "event": "anomaly_found",
                    "type": "hidden_process",
                    "pid": pid,
                    "name": hidden_proc["name"],
                    "score": 50,
                })

        # Step 4: Process cmdline data
        cmdline_output = plugin_results.get("windows.cmdline", [])
        cmdline_map = {}
        for entry in cmdline_output:
            pid = entry.get("PID", entry.get("pid", 0))
            cmdline_map[pid] = entry.get("Args", entry.get("args", ""))

        # Step 5: Process malfind data
        malfind_output = plugin_results.get("windows.malfind", [])
        malfind_by_pid: Dict[int, List[Dict]] = {}
        for entry in malfind_output:
            pid = entry.get("PID", entry.get("pid", 0))
            if pid not in malfind_by_pid:
                malfind_by_pid[pid] = []
            malfind_by_pid[pid].append({
                "pid": pid,
                "process_name": entry.get("Process", entry.get("process_name", "")),
                "address": entry.get("Address", entry.get("address", "")),
                "size": entry.get("Size", entry.get("size", 0)),
                "protection": entry.get("Protection", entry.get("protection", "")),
                "hex_dump": entry.get("Hexdump", entry.get("hex_dump", "")),
                "disassembly": entry.get("Disasm", entry.get("disassembly", "")),
                "tag": entry.get("Tag", entry.get("tag", "")),
            })

        # Step 6: Process network data
        netscan_output = plugin_results.get("windows.netscan", [])
        connections_by_pid: Dict[int, List[Dict]] = {}
        all_connections = []

        for entry in netscan_output:
            pid = entry.get("PID", entry.get("pid", 0)) or 0
            local_port = entry.get("LocalPort", entry.get("local_port", 0)) or 0
            remote_port = entry.get("ForeignPort", entry.get("remote_port", 0)) or 0
            local_addr = entry.get("LocalAddr", entry.get("local_addr", "")) or ""
            remote_addr = entry.get("ForeignAddr", entry.get("remote_addr", "")) or ""

            # Ensure ports are integers (Volatility can return strings)
            try:
                local_port = int(local_port)
            except (ValueError, TypeError):
                local_port = 0
            try:
                remote_port = int(remote_port)
            except (ValueError, TypeError):
                remote_port = 0

            conn = {
                "pid": pid,
                "protocol": entry.get("Proto", entry.get("protocol", "TCP")) or "TCP",
                "local_addr": str(local_addr),
                "local_port": local_port,
                "remote_addr": str(remote_addr),
                "remote_port": remote_port,
                "state": entry.get("State", entry.get("state", "")) or "",
                "is_suspicious_port": local_port in SUSPICIOUS_PORTS or remote_port in SUSPICIOUS_PORTS,
            }

            if pid not in connections_by_pid:
                connections_by_pid[pid] = []
            connections_by_pid[pid].append(conn)
            all_connections.append(conn)

        # Step 7: Run scoring engine
        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 88,
            "message": "Running scoring engine — calculating suspicion scores...",
        })

        # Build process map for parent resolution
        all_processes_map = {
            p["pid"]: p for p in diff_result["merged_processes"]
        }

        scored_processes = []
        max_score = 0
        suspicious_count = 0

        for proc in diff_result["merged_processes"]:
            pid = proc["pid"]

            # Attach cmdline
            proc["cmdline"] = cmdline_map.get(pid, "")

            # Get connections and malfind for this PID
            pid_connections = connections_by_pid.get(pid, [])
            pid_malfind = malfind_by_pid.get(pid, [])

            # Calculate score
            score_result = calculate_score(
                proc, pid_connections, pid_malfind, all_processes_map
            )

            proc["suspicion_score"] = score_result["total_score"]
            proc["status"] = score_result["status"]
            proc["has_injected_code"] = len(pid_malfind) > 0
            proc["score_breakdown"] = score_result["breakdown"]

            scored_processes.append(proc)

            if score_result["total_score"] > max_score:
                max_score = score_result["total_score"]
            if score_result["total_score"] >= 30:
                suspicious_count += 1

        # Step 8: GeoIP resolution
        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 92,
            "message": "Resolving IP geolocation...",
        })

        remote_ips = list(set(
            c["remote_addr"] for c in all_connections
            if c.get("remote_addr") and c["remote_addr"] not in ("0.0.0.0", "*", "")
        ))

        geo_results = await resolve_ips_batch(remote_ips, db)

        # Attach GeoIP to connections
        for conn in all_connections:
            remote = conn.get("remote_addr", "")
            if remote in geo_results and geo_results[remote]:
                geo = geo_results[remote]
                conn["country"] = geo.get("country")
                conn["city"] = geo.get("city")
                conn["lat"] = geo.get("lat")
                conn["lon"] = geo.get("lon")

        # Step 9: Save to database
        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 95,
            "message": "Saving analysis results to database...",
        })

        risk_level = determine_risk_level(
            diff_result["hidden_count"], max_score, suspicious_count
        )

        # Update analysis record
        analysis.status = "complete"
        analysis.risk_level = risk_level
        analysis.hidden_process_count = diff_result["hidden_count"]
        analysis.total_process_count = diff_result["total_count"]
        analysis.suspicious_connection_count = sum(
            1 for c in all_connections if c.get("is_suspicious_port")
        )
        analysis.completed_at = datetime.utcnow()
        analysis.os_profile = "Windows (Mock)" if settings.MOCK_MODE else "Windows (Auto-detected)"

        # Save processes
        for proc in scored_processes:
            db_proc = Process(
                analysis_id=analysis_id,
                pid=proc["pid"],
                ppid=proc.get("ppid"),
                name=proc["name"],
                in_pslist=proc["in_pslist"],
                in_psscan=proc["in_psscan"],
                is_hidden=proc["is_hidden"],
                cmdline=proc.get("cmdline"),
                suspicion_score=proc["suspicion_score"],
                status=proc["status"],
                has_injected_code=proc.get("has_injected_code", False),
                create_time=proc.get("create_time"),
                offset=proc.get("offset"),
            )
            db.add(db_proc)

        # Save network connections
        for conn in all_connections:
            # Find process name
            proc_name = all_processes_map.get(conn["pid"], {}).get("name", "Unknown")
            db_conn = NetworkConnection(
                analysis_id=analysis_id,
                pid=conn["pid"],
                process_name=proc_name,
                protocol=conn["protocol"],
                local_addr=conn["local_addr"],
                local_port=conn["local_port"],
                remote_addr=conn.get("remote_addr"),
                remote_port=conn.get("remote_port"),
                state=conn.get("state"),
                country=conn.get("country"),
                city=conn.get("city"),
                lat=conn.get("lat"),
                lon=conn.get("lon"),
                is_suspicious_port=conn.get("is_suspicious_port", False),
            )
            db.add(db_conn)

        # Save memory regions
        for pid, regions in malfind_by_pid.items():
            for region in regions:
                db_region = MemoryRegion(
                    analysis_id=analysis_id,
                    pid=pid,
                    process_name=region.get("process_name"),
                    address=region.get("address", ""),
                    size=region.get("size"),
                    protection=region.get("protection"),
                    hex_dump=region.get("hex_dump"),
                    disassembly=region.get("disassembly"),
                    tag=region.get("tag"),
                )
                db.add(db_region)

        await db.commit()

        # Step 10: Broadcast completion
        await ws_broadcast(analysis_id, {
            "event": "analysis_complete",
            "analysis_id": analysis_id,
            "risk_level": risk_level,
            "hidden_count": diff_result["hidden_count"],
            "total_processes": diff_result["total_count"],
        })

        await ws_broadcast(analysis_id, {
            "event": "progress",
            "percent": 100,
            "message": f"🎯 Analysis complete — Risk Level: {risk_level.upper()} | {diff_result['hidden_count']} hidden process(es) found",
        })

        logger.info(
            f"Analysis {analysis_id} complete: "
            f"risk={risk_level}, hidden={diff_result['hidden_count']}, "
            f"total={diff_result['total_count']}"
        )

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)

        # Update status to failed
        try:
            analysis = await db.get(Analysis, analysis_id)
            if analysis:
                analysis.status = "failed"
                await db.commit()
        except Exception:
            pass

        await ws_broadcast(analysis_id, {
            "event": "plugin_error",
            "plugin": "pipeline",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        })
