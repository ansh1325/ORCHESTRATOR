"""
Pydantic Schemas for LlamaOrchestrator
Defines data structures for Intent Analysis, Knowledge Base, DAG Planning,
Worker Specs, and Real-time SSE Events.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class ClarificationQuestion(BaseModel):
    id: str
    question: str
    why_needed: str
    options: List[str]
    default_selection: str

class IntentAnalysis(BaseModel):
    session_id: str
    track_type: str = Field(description="business_acquisition | technical_software | communication_assistant | robotics_humanoid | general")
    combat_tier: str = Field(default="tactical_squad", description="solo | tactical_squad | swarm_army")
    swarm_size_descriptor: str = Field(default="Tactical Squad (3-4 Specialized Agents)")
    raw_vision: str
    extracted_goals: List[str]
    identified_constraints: List[str]
    missing_parameters: List[str]
    clarifications: List[ClarificationQuestion]
    recommended_defaults: Dict[str, str]
    created_at: str = Field(default_factory=utc_now_iso)

class ClarificationResponse(BaseModel):
    session_id: str
    auto_approve: bool = False
    answers: Dict[str, str] = Field(default_factory=dict)

class KnowledgeBase(BaseModel):
    session_id: str
    target_niche: str
    icp: Dict[str, Any] = Field(description="Ideal Customer Profile: roles, company size, pain points")
    pricing_tiers: List[Dict[str, Any]]
    milestone_1: str
    milestone_2: str
    technical_blueprint: Dict[str, Any]
    scraped_sources: List[Dict[str, str]]
    synthesis_summary: str
    updated_at: str = Field(default_factory=utc_now_iso)

class TaskNode(BaseModel):
    id: str
    title: str
    agent_type: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    status: str = Field(default="pending", description="pending | running | completed | failed | self_correcting")
    assigned_tools: List[str] = Field(default_factory=list)
    output_artifacts: List[str] = Field(default_factory=list)
    execution_logs: List[str] = Field(default_factory=list)
    retry_count: int = 0
    error_feedback: Optional[str] = None

class DAGPlan(BaseModel):
    session_id: str
    title: str
    objective: str
    nodes: List[TaskNode]
    estimated_duration_sec: int = 30
    is_validated: bool = True
    created_at: str = Field(default_factory=utc_now_iso)

class SubAgentSpec(BaseModel):
    agent_id: str
    name: str
    role: str
    system_prompt: str
    allowed_tools: List[str]
    model: str = "llama-3.1-8b-instant"

class ExecutionEvent(BaseModel):
    event_type: str = Field(description="stage_change | log | clarification_needed | kb_updated | dag_generated | task_start | task_progress | task_complete | self_correction | evaluation_passed | voice_speech | done | error")
    timestamp: str = Field(default_factory=utc_now_iso)
    session_id: str
    stage: int = 0
    stage_name: str = "Central Brain"
    task_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    message: str
    speech_text: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

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
    artifacts: List[str] = Field(default_factory=list)

class SavedWorkflow(BaseModel):
    id: str
    title: str
    description: str
    prompt_template: str
    folder: str = "Workflows"

class ScheduledTask(BaseModel):
    task_id: str
    title: str
    prompt: str
    schedule_cron: str = "Daily 6:00 AM"
    is_active: bool = True
    created_at: str = Field(default_factory=utc_now_iso)

class FolderUpdateRequest(BaseModel):
    session_id: str
    folder: str

class PinUpdateRequest(BaseModel):
    session_id: str
    is_pinned: bool

class AnalyzeRequest(BaseModel):
    vision: str
    session_id: Optional[str] = None

class LaunchRequest(BaseModel):
    session_id: str
    auto_approve: bool = True
    answers: Optional[Dict[str, str]] = None
