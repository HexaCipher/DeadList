"""
DeadList Analysis Router
REST endpoints for fetching analysis results, history, process details, and PDF reports.
"""

import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from models.database import Analysis, Process, NetworkConnection, MemoryRegion, get_db
from models.schemas import (
    AnalysisResponse, AnalysisSummary, ProcessResponse,
    ProcessDetailResponse, NetworkConnectionResponse,
    MemoryRegionResponse, HealthResponse, ScoreComponent,
    VolatilityStatus,
)
from core.pdf_generator import generate_report
from core.volatility_runner import check_volatility_available
from core.scoring_engine import calculate_score, SUSPICIOUS_PORTS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


# ─── Health ───────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    vol_info = check_volatility_available()
    return HealthResponse(
        status="ok",
        volatility=VolatilityStatus(**vol_info),
        mock_mode=settings.MOCK_MODE,
        version="1.0.0",
    )


# ─── Full Analysis ───────────────────────────────────────────

@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Get full analysis with all processes, connections, and memory regions."""
    result = await db.execute(
        select(Analysis)
        .options(
            selectinload(Analysis.processes),
            selectinload(Analysis.connections),
            selectinload(Analysis.memory_regions),
        )
        .where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return analysis


# ─── Processes ───────────────────────────────────────────────

@router.get("/analysis/{analysis_id}/processes", response_model=list[ProcessResponse])
async def get_processes(
    analysis_id: str,
    status: Optional[str] = Query(None, description="Filter by status: hidden, suspicious, clean"),
    min_score: Optional[int] = Query(None, description="Minimum suspicion score"),
    search: Optional[str] = Query(None, description="Search process name"),
    sort_by: str = Query("suspicion_score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: AsyncSession = Depends(get_db),
):
    """Get processes for an analysis with filtering and sorting."""
    query = select(Process).where(Process.analysis_id == analysis_id)

    if status:
        query = query.where(Process.status == status)
    if min_score is not None:
        query = query.where(Process.suspicion_score >= min_score)
    if search:
        query = query.where(Process.name.ilike(f"%{search}%"))

    # Sorting
    sort_column = getattr(Process, sort_by, Process.suspicion_score)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    result = await db.execute(query)
    processes = result.scalars().all()

    return processes


@router.get("/analysis/{analysis_id}/process/{pid}")
async def get_process_detail(
    analysis_id: str,
    pid: int,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information for a single process including connections and memory regions."""
    # Get process
    proc_result = await db.execute(
        select(Process).where(
            Process.analysis_id == analysis_id,
            Process.pid == pid,
        )
    )
    process = proc_result.scalar_one_or_none()

    if not process:
        raise HTTPException(status_code=404, detail=f"Process with PID {pid} not found")

    # Get connections for this PID
    conn_result = await db.execute(
        select(NetworkConnection).where(
            NetworkConnection.analysis_id == analysis_id,
            NetworkConnection.pid == pid,
        )
    )
    connections = conn_result.scalars().all()

    # Get memory regions for this PID
    mem_result = await db.execute(
        select(MemoryRegion).where(
            MemoryRegion.analysis_id == analysis_id,
            MemoryRegion.pid == pid,
        )
    )
    memory_regions = mem_result.scalars().all()

    # Rebuild score breakdown
    proc_dict = {
        "pid": process.pid,
        "name": process.name,
        "ppid": process.ppid,
        "is_hidden": process.is_hidden,
        "cmdline": process.cmdline,
    }
    conn_dicts = [
        {
            "local_port": c.local_port,
            "remote_port": c.remote_port,
            "remote_addr": c.remote_addr,
        }
        for c in connections
    ]
    malfind_dicts = [{"pid": m.pid} for m in memory_regions]

    score_result = calculate_score(proc_dict, conn_dicts, malfind_dicts)

    return {
        "id": process.id,
        "pid": process.pid,
        "ppid": process.ppid,
        "name": process.name,
        "in_pslist": process.in_pslist,
        "in_psscan": process.in_psscan,
        "is_hidden": process.is_hidden,
        "cmdline": process.cmdline,
        "suspicion_score": process.suspicion_score,
        "status": process.status,
        "has_injected_code": process.has_injected_code,
        "create_time": process.create_time,
        "offset": process.offset,
        "connections": [NetworkConnectionResponse.model_validate(c) for c in connections],
        "memory_regions": [MemoryRegionResponse.model_validate(m) for m in memory_regions],
        "score_breakdown": score_result["breakdown"],
    }


# ─── Network ─────────────────────────────────────────────────

@router.get("/analysis/{analysis_id}/network", response_model=list[NetworkConnectionResponse])
async def get_network_connections(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all network connections for an analysis with GeoIP data."""
    result = await db.execute(
        select(NetworkConnection)
        .where(NetworkConnection.analysis_id == analysis_id)
        .order_by(desc(NetworkConnection.is_suspicious_port))
    )
    return result.scalars().all()


# ─── PDF Report ───────────────────────────────────────────────

@router.get("/analysis/{analysis_id}/report/pdf")
async def download_pdf_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Generate and download a PDF analysis report."""
    # Get full analysis data
    result = await db.execute(
        select(Analysis)
        .options(
            selectinload(Analysis.processes),
            selectinload(Analysis.connections),
            selectinload(Analysis.memory_regions),
        )
        .where(Analysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if analysis.status != "complete":
        raise HTTPException(status_code=400, detail="Analysis is not yet complete")

    # Build data dict for PDF generator
    analysis_data = {
        "filename": analysis.filename,
        "md5_hash": analysis.md5_hash,
        "sha256_hash": analysis.sha256_hash,
        "file_size_bytes": analysis.file_size_bytes,
        "created_at": analysis.created_at.strftime("%Y-%m-%d %H:%M:%S") if analysis.created_at else "N/A",
        "status": analysis.status,
        "risk_level": analysis.risk_level or "unknown",
        "os_profile": analysis.os_profile,
        "hidden_process_count": analysis.hidden_process_count,
        "total_process_count": analysis.total_process_count,
        "suspicious_connection_count": analysis.suspicious_connection_count,
        "processes": [
            {
                "pid": p.pid,
                "name": p.name,
                "ppid": p.ppid,
                "status": p.status,
                "suspicion_score": p.suspicion_score,
                "is_hidden": p.is_hidden,
                "cmdline": p.cmdline,
            }
            for p in analysis.processes
        ],
        "connections": [
            {
                "pid": c.pid,
                "protocol": c.protocol,
                "local_addr": c.local_addr,
                "local_port": c.local_port,
                "remote_addr": c.remote_addr,
                "remote_port": c.remote_port,
                "state": c.state,
                "is_suspicious_port": c.is_suspicious_port,
            }
            for c in analysis.connections
        ],
        "memory_regions": [
            {
                "pid": m.pid,
                "process_name": m.process_name,
                "address": m.address,
                "size": m.size,
                "protection": m.protection,
                "hex_dump": m.hex_dump,
                "tag": m.tag,
            }
            for m in analysis.memory_regions
        ],
    }

    # Generate PDF
    pdf_bytes = generate_report(analysis_data)

    filename = f"DeadList_Report_{analysis.filename}_{analysis.created_at.strftime('%Y%m%d_%H%M%S')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ─── History ──────────────────────────────────────────────────

@router.get("/history", response_model=list[AnalysisSummary])
async def get_analysis_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of past analysis runs."""
    offset = (page - 1) * limit

    result = await db.execute(
        select(Analysis)
        .order_by(desc(Analysis.created_at))
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()


# ─── Delete ───────────────────────────────────────────────────

@router.delete("/analysis/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an analysis and its associated dump file."""
    analysis = await db.get(Analysis, analysis_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Delete dump file
    if analysis.filepath and os.path.exists(analysis.filepath):
        try:
            os.remove(analysis.filepath)
        except Exception as e:
            logger.warning(f"Failed to delete dump file: {e}")

    # Delete analysis (cascade deletes processes, connections, regions)
    await db.delete(analysis)
    await db.commit()

    return {"message": f"Analysis {analysis_id} deleted successfully"}
