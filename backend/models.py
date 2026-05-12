from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class IncidentInput(BaseModel):
    incident_id: str
    timestamp: datetime
    device: str
    alert_type: str
    raw_message: str
    affected_peer: Optional[str] = None
    severity: SeverityLevel

class Hypothesis(BaseModel):
    cause: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str]
    reasoning: str

class RemediationAction(BaseModel):
    action_id: str
    description: str
    commands: List[str]
    risk_level: RiskLevel
    rollback_commands: List[str]
    requires_approval: bool

class AuditEntry(BaseModel):
    incident_id: str
    timestamp: datetime
    observe_output: str
    hypothesis: Hypothesis
    validation_result: str
    remediation: RemediationAction
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    outcome: Optional[str] = None

class ApprovalRequest(BaseModel):
    incident_id: str
    approved: bool
    approved_by: str = "human_operator"