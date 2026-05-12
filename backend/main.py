import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from graph import build_graph, NOCState
from db import init_db, get_all_audits, get_audit, update_approval
from models import ApprovalRequest

app = FastAPI(title="NOC Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
noc_graph = build_graph()
executor = ThreadPoolExecutor(max_workers=2)
active_incidents: dict[str, NOCState] = {}


@app.get("/")
def root():
    return {"status": "NOC Agent running", "version": "1.0.0"}


@app.post("/incidents/trigger-async")
async def trigger_incident_async(incident_file: str = "incidents/bgp_down.json"):
    """Non-blocking — runs agent in background thread so browser doesn't freeze."""
    if not os.path.exists(incident_file):
        raise HTTPException(status_code=404, detail=f"File not found: {incident_file}")

    initial_state: NOCState = {
        "incident_path": incident_file,
        "incident": None,
        "observation_summary": None,
        "hypothesis": None,
        "remediation": None,
        "requires_human": False,
        "approved": None,
        "completed": False
    }

    loop = asyncio.get_event_loop()
    final_state = await loop.run_in_executor(
        executor, lambda: noc_graph.invoke(initial_state)
    )

    incident_id = final_state["incident"].incident_id
    active_incidents[incident_id] = final_state

    return {
        "incident_id": incident_id,
        "status": "awaiting_approval" if final_state["requires_human"] else "auto_remediated",
        "requires_human": final_state["requires_human"],
        "hypothesis": {
            "cause": final_state["hypothesis"].cause,
            "confidence": final_state["hypothesis"].confidence,
            "evidence": final_state["hypothesis"].evidence,
            "reasoning": final_state["hypothesis"].reasoning
        },
        "remediation": {
            "action_id": final_state["remediation"].action_id,
            "description": final_state["remediation"].description,
            "commands": final_state["remediation"].commands,
            "risk_level": final_state["remediation"].risk_level,
            "rollback_commands": final_state["remediation"].rollback_commands,
            "requires_approval": final_state["remediation"].requires_approval
        }
    }


@app.post("/incidents/{incident_id}/approve")
def approve_incident(incident_id: str, request: ApprovalRequest):
    if incident_id not in active_incidents:
        raise HTTPException(status_code=404, detail="Incident not found in active queue")
    update_approval(incident_id, request.approved, request.approved_by)
    active_incidents[incident_id]["approved"] = request.approved
    action = "APPROVED ✅" if request.approved else "REJECTED ❌"
    return {
        "incident_id": incident_id,
        "action": action,
        "approved_by": request.approved_by,
        "message": f"Remediation {action} by {request.approved_by}"
    }


@app.get("/incidents")
def list_incidents():
    rows = get_all_audits()
    incidents = []
    for row in rows:
        incidents.append({
            "id": row[0],
            "incident_id": row[1],
            "timestamp": row[2],
            "observe_output": row[3],
            "hypothesis": json.loads(row[4]) if row[4] else None,
            "validation_result": row[5],
            "remediation": json.loads(row[6]) if row[6] else None,
            "approved": bool(row[7]) if row[7] is not None else None,
            "approved_by": row[8],
            "outcome": row[9],
            "created_at": row[10]
        })
    return {"incidents": incidents, "total": len(incidents)}


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    rows = get_audit(incident_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Incident not found")
    row = rows[0]
    return {
        "incident_id": row[1],
        "timestamp": row[2],
        "hypothesis": json.loads(row[4]) if row[4] else None,
        "remediation": json.loads(row[6]) if row[6] else None,
        "approved": bool(row[7]) if row[7] is not None else None,
        "outcome": row[9]
    }