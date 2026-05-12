import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import TypedDict, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END

from models import IncidentInput, Hypothesis, RemediationAction, AuditEntry
from nodes.observe import observe_incident
from nodes.hypothesize import hypothesize
from nodes.remediate import remediate
from db import init_db, save_audit

# ── State shared across all nodes ──────────────────────────────────────────
class NOCState(TypedDict):
    incident_path: str
    incident: Optional[IncidentInput]
    observation_summary: Optional[str]
    hypothesis: Optional[Hypothesis]
    remediation: Optional[RemediationAction]
    requires_human: bool
    approved: Optional[bool]
    completed: bool

# ── Node functions ──────────────────────────────────────────────────────────
def node_observe(state: NOCState) -> NOCState:
    print("\n[1/4] 🔍 OBSERVING incident...")
    incident, summary = observe_incident(state["incident_path"])
    print(summary)
    return {**state, "incident": incident, "observation_summary": summary}

def node_hypothesize(state: NOCState) -> NOCState:
    print("\n[2/4] 🧠 HYPOTHESIZING root cause (Claude)...")
    hypothesis = hypothesize(state["observation_summary"])
    print(f"  Root Cause : {hypothesis.cause}")
    print(f"  Confidence : {hypothesis.confidence * 100:.0f}%")
    for e in hypothesis.evidence:
        print(f"  Evidence   : {e}")
    return {**state, "hypothesis": hypothesis}

def node_remediate(state: NOCState) -> NOCState:
    print("\n[3/4] 🔧 GENERATING remediation plan (Claude)...")
    remediation = remediate(
        state["incident"].incident_id,
        state["hypothesis"],
        state["incident"].device
    )
    print(f"  Action     : {remediation.description}")
    print(f"  Risk Level : {remediation.risk_level.upper()}")
    print(f"  Commands   : {remediation.commands}")
    print(f"  Needs Approval: {remediation.requires_approval}")
    return {**state, "remediation": remediation, 
            "requires_human": remediation.requires_approval}

def node_save_audit(state: NOCState) -> NOCState:
    print("\n[4/4] 📋 SAVING audit trail...")
    entry = AuditEntry(
        incident_id=state["incident"].incident_id,
        timestamp=datetime.now(),
        observe_output=state["observation_summary"],
        hypothesis=state["hypothesis"],
        validation_result="Batfish validation skipped for demo",
        remediation=state["remediation"],
        approved=state.get("approved"),
        approved_by="human_operator" if state.get("approved") else None,
        outcome="Pending approval" if state["requires_human"] else "Auto-remediated"
    )
    init_db()
    save_audit(entry)
    print(f"  Audit saved for incident: {entry.incident_id}")
    return {**state, "completed": True}

# ── Routing logic ───────────────────────────────────────────────────────────
def route_after_remediate(state: NOCState) -> str:
    if state["requires_human"]:
        print("\n⚠️  HIGH/MEDIUM RISK — Pausing for human approval...")
        return "save_audit"
    return "save_audit"

# ── Build the graph ─────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(NOCState)

    graph.add_node("observe", node_observe)
    graph.add_node("hypothesize", node_hypothesize)
    graph.add_node("remediate", node_remediate)
    graph.add_node("save_audit", node_save_audit)

    graph.set_entry_point("observe")
    graph.add_edge("observe", "hypothesize")
    graph.add_edge("hypothesize", "remediate")
    graph.add_conditional_edges("remediate", route_after_remediate,
                                 {"save_audit": "save_audit"})
    graph.add_edge("save_audit", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()

    initial_state: NOCState = {
        "incident_path": "incidents/bgp_down.json",
        "incident": None,
        "observation_summary": None,
        "hypothesis": None,
        "remediation": None,
        "requires_human": False,
        "approved": None,
        "completed": False
    }

    print("=" * 60)
    print("   NOC AGENT — EXPLAINABLE INCIDENT RESPONSE")
    print("=" * 60)

    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("   AGENT COMPLETE")
    print("=" * 60)
    if final_state["requires_human"]:
        print("🔴 ACTION REQUIRED: Human approval needed before remediation executes.")
        print(f"   Incident ID : {final_state['incident'].incident_id}")
        print(f"   Risk Level  : {final_state['remediation'].risk_level.upper()}")
        print(f"   Fix         : {final_state['remediation'].description}")
    else:
        print("✅ Auto-remediated successfully.")