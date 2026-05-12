import json
from pathlib import Path
from models import IncidentInput, SeverityLevel
from datetime import datetime

def observe_incident(incident_path: str) -> tuple[IncidentInput, str]:
    """
    Node 1: OBSERVE
    Load and parse the raw incident. Extract key signals.
    Returns the structured incident + a human-readable observation summary.
    """
    with open(incident_path) as f:
        raw = json.load(f)

    incident = IncidentInput(
        incident_id=raw["incident_id"],
        timestamp=datetime.fromisoformat(raw["timestamp"]),
        device=raw["device"],
        alert_type=raw["alert_type"],
        raw_message=raw["raw_message"],
        affected_peer=raw.get("affected_peer"),
        severity=SeverityLevel(raw["severity"])
    )

    context = raw.get("context", {})

    # Extract key signals for the LLM
    signals = []

    if context.get("last_config_change_by", "").startswith("neteng-auto"):
        signals.append("⚠️  Last config change made by an AUTOMATED AGENT")

    last_change = context.get("last_config_change")
    if last_change:
        change_time = datetime.fromisoformat(last_change)
        delta = incident.timestamp - change_time
        minutes = int(delta.total_seconds() / 60)
        signals.append(f"⏱  Config change was {minutes} minutes before incident")

    local_mtu = context.get("mtu")
    peer_mtu = context.get("peer_mtu")
    if local_mtu and peer_mtu and local_mtu != peer_mtu:
        signals.append(f"🔴 MTU MISMATCH: local={local_mtu} peer={peer_mtu}")

    if context.get("interface_status") == "up":
        signals.append("✅ Physical interface is UP — not a hardware failure")

    recent_events = context.get("recent_events", [])
    if recent_events:
        signals.append(f"📋 {len(recent_events)} recent events logged")

    observation_summary = f"""
INCIDENT OBSERVED: {incident.incident_id}
Device: {incident.device}
Alert: {incident.alert_type}
Peer: {incident.affected_peer}
Severity: {incident.severity.upper()}
Raw Message: {incident.raw_message}

KEY SIGNALS DETECTED:
{chr(10).join(signals)}

RECENT EVENT TIMELINE:
{chr(10).join(recent_events)}
""".strip()

    return incident, observation_summary


if __name__ == "__main__":
    incident, summary = observe_incident("incidents/bgp_down.json")
    print(summary)