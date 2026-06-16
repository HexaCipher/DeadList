"""
DeadList Pydantic Schemas
Request/response validation and serialization for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Analysis Schemas ────────────────────────────────────────

class AnalysisCreate(BaseModel):
    """Response returned after upload."""
    analysis_id: str
    filename: str
    md5: str
    sha256: str
    file_size_bytes: int
    status: str = "pending"


class AnalysisResponse(BaseModel):
    """Full analysis response with all data."""
    id: str
    filename: str
    filepath: str
    md5_hash: str
    sha256_hash: str
    file_size_bytes: int
    status: str
    risk_level: Optional[str] = None
    hidden_process_count: Optional[int] = 0
    total_process_count: Optional[int] = 0
    suspicious_connection_count: Optional[int] = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    os_profile: Optional[str] = None
    processes: List["ProcessResponse"] = []
    connections: List["NetworkConnectionResponse"] = []
    memory_regions: List["MemoryRegionResponse"] = []

    model_config = {"from_attributes": True}


class AnalysisSummary(BaseModel):
    """Lightweight summary for history list."""
    id: str
    filename: str
    file_size_bytes: int
    status: str
    risk_level: Optional[str] = None
    hidden_process_count: Optional[int] = 0
    total_process_count: Optional[int] = 0
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Process Schemas ─────────────────────────────────────────

class ProcessResponse(BaseModel):
    """Single process from analysis."""
    id: int
    pid: int
    ppid: Optional[int] = None
    name: str
    in_pslist: bool
    in_psscan: bool
    is_hidden: bool
    cmdline: Optional[str] = None
    suspicion_score: int = 0
    status: str = "clean"
    has_injected_code: bool = False
    create_time: Optional[str] = None
    offset: Optional[str] = None

    model_config = {"from_attributes": True}


class ProcessDetailResponse(ProcessResponse):
    """Extended process detail with connections and memory regions."""
    connections: List["NetworkConnectionResponse"] = []
    memory_regions: List["MemoryRegionResponse"] = []
    score_breakdown: List["ScoreComponent"] = []


# ─── Network Connection Schemas ──────────────────────────────

class NetworkConnectionResponse(BaseModel):
    """Network connection from netscan."""
    id: int
    pid: int
    process_name: Optional[str] = None
    protocol: str
    local_addr: str
    local_port: int
    remote_addr: Optional[str] = None
    remote_port: Optional[int] = None
    state: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    is_suspicious_port: bool = False

    model_config = {"from_attributes": True}


# ─── Memory Region Schemas ───────────────────────────────────

class MemoryRegionResponse(BaseModel):
    """Suspicious memory region from malfind."""
    id: int
    pid: int
    process_name: Optional[str] = None
    address: str
    size: Optional[int] = None
    protection: Optional[str] = None
    hex_dump: Optional[str] = None
    disassembly: Optional[str] = None
    tag: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Scoring Schemas ─────────────────────────────────────────

class ScoreComponent(BaseModel):
    """Individual scoring criterion result."""
    criterion: str
    points: int
    severity: str  # CRITICAL / HIGH / MEDIUM / LOW
    description: str


# ─── WebSocket Event Schemas ─────────────────────────────────

class WSPluginStarted(BaseModel):
    event: str = "plugin_started"
    plugin: str
    timestamp: str


class WSPluginComplete(BaseModel):
    event: str = "plugin_complete"
    plugin: str
    timestamp: str
    count: int = 0


class WSPluginError(BaseModel):
    event: str = "plugin_error"
    plugin: str
    timestamp: str
    error: str


class WSAnomalyFound(BaseModel):
    event: str = "anomaly_found"
    type: str
    pid: int
    name: str
    score: int


class WSAnalysisComplete(BaseModel):
    event: str = "analysis_complete"
    analysis_id: str
    risk_level: str
    hidden_count: int
    total_processes: int


class WSProgress(BaseModel):
    event: str = "progress"
    percent: int
    message: str


# ─── Health Schema ───────────────────────────────────────────

class VolatilityStatus(BaseModel):
    available: bool = False
    mode: str = "mock"
    message: str = ""
    binary: Optional[str] = None

class HealthResponse(BaseModel):
    status: str = "ok"
    volatility: VolatilityStatus = VolatilityStatus()
    mock_mode: bool = True
    version: str = "1.0.0"

