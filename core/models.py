"""
Pydantic Schemas for LlamaOrchestrator
Defines data structures for Intent Analysis, Knowledge Base, DAG Planning,
Worker Specs, and Real-time SSE Events.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()

class ClarificationQuestion(BaseModel):
    id: str
    question: str
    why_needed: str
    options: list[str]
    default_selection: str

class IntentAnalysis(BaseModel):
    session_id: str
    track_type: str = Field(description="business_acquisition | technical_software | communication_assistant | robotics_humanoid | quantitative_trading | general")
    combat_tier: str = Field(default="tactical_squad", description="solo | tactical_squad | swarm_army")
    swarm_size_descriptor: str = Field(default="Tactical Squad (3-4 Specialized Agents)")
    response_mode: str = Field(default="swarm_army", description="direct_response | swarm_army")
    raw_vision: str
    extracted_goals: list[str]
    identified_constraints: list[str]
    missing_parameters: list[str]
    clarifications: list[ClarificationQuestion]
    recommended_defaults: dict[str, str]
    created_at: str = Field(default_factory=utc_now_iso)

class ClarificationResponse(BaseModel):
    session_id: str
    auto_approve: bool = False
    answers: dict[str, str] = Field(default_factory=dict)

class KnowledgeBase(BaseModel):
    session_id: str
    target_niche: str
    icp: dict[str, Any] = Field(description="Ideal Customer Profile: roles, company size, pain points")
    pricing_tiers: list[dict[str, Any]]
    milestone_1: str
    milestone_2: str
    technical_blueprint: dict[str, Any]
    scraped_sources: list[dict[str, str]]
    synthesis_summary: str
    omnichannel_channels: list[dict[str, Any]] = Field(default_factory=list, description="Targeted channels: LinkedIn browser automation, Twitter/X DMs, community groups, and cold email")
    ready_for_permission_actions: list[dict[str, Any]] = Field(default_factory=list, description="Pre-staged autonomous actions awaiting 1-click user authorization")
    updated_at: str = Field(default_factory=utc_now_iso)

class TaskNode(BaseModel):
    id: str
    title: str
    agent_type: str
    description: str
    dependencies: list[str] = Field(default_factory=list)
    status: str = Field(default="pending", description="pending | running | completed | failed | self_correcting")
    assigned_tools: list[str] = Field(default_factory=list)
    output_artifacts: list[str] = Field(default_factory=list)
    execution_logs: list[str] = Field(default_factory=list)
    retry_count: int = 0
    error_feedback: str | None = None

class DAGPlan(BaseModel):
    session_id: str
    title: str
    objective: str
    nodes: list[TaskNode]
    estimated_duration_sec: int = 30
    is_validated: bool = True
    created_at: str = Field(default_factory=utc_now_iso)

class SubAgentSpec(BaseModel):
    agent_id: str
    name: str
    role: str
    system_prompt: str
    allowed_tools: list[str]
    model: str = "llama-3.1-8b-instant"

class ExecutionEvent(BaseModel):
    event_type: str = Field(description="stage_change | log | clarification_needed | kb_updated | dag_generated | task_start | task_progress | task_complete | self_correction | evaluation_passed | voice_speech | done | error")
    timestamp: str = Field(default_factory=utc_now_iso)
    session_id: str
    stage: int = 0
    stage_name: str = "Central Brain"
    task_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    message: str
    speech_text: str | None = None

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    role: str = "assistant"
    text: str
    speech_audio: str
    speaker: str = "LlamaOrchestrator (Central Brain)"

class HistoryItem(BaseModel):
    session_id: str
    title: str
    prompt: str
    folder: str = "General"
    is_pinned: bool = False
    status: str = "completed"
    created_at: str = Field(default_factory=utc_now_iso)
    artifacts: list[str] = Field(default_factory=list)

class SavedWorkflow(BaseModel):
    id: str
    title: str
    description: str = ""
    prompt: str = ""
    prompt_template: str = ""
    folder: str = "Workflows"
    created_at: str = Field(default_factory=utc_now_iso)

class ScheduledTask(BaseModel):
    task_id: str
    title: str
    prompt: str
    schedule_cron: str = "Daily 6:00 AM"
    hour: int = 6
    minute: int = 0
    is_active: bool = True
    created_at: str = Field(default_factory=utc_now_iso)
    last_run_at: str | None = None
    last_run_date: str | None = None
    run_count: int = 0

class FolderUpdateRequest(BaseModel):
    session_id: str
    folder: str

class PinUpdateRequest(BaseModel):
    session_id: str
    is_pinned: bool

class AnalyzeRequest(BaseModel):
    vision: str
    session_id: str | None = None

class LaunchRequest(BaseModel):
    session_id: str
    auto_approve: bool = True
    answers: dict[str, str] | None = None

class ImportPathRequest(BaseModel):
    source_path: str
    target_name: str | None = None

class ExportPathRequest(BaseModel):
    destination_path: str | None = None
