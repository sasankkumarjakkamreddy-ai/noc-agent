import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import uuid
import anthropic
from models import Hypothesis, RemediationAction, RiskLevel

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert L3 Network Engineer generating safe, 
precise remediation actions for network incidents.

For every remediation you provide:
1. Exact CLI commands to fix the issue (Cisco IOS XR syntax)
2. Exact rollback commands to undo the fix if it fails
3. A risk assessment (low/medium/high)
4. Whether human approval is required before execution

Risk rules:
- low: read-only commands, show commands, soft resets
- medium: BGP session resets, interface bounces, timer changes
- high: routing policy changes, prefix list changes, BGP neighbor removal

Require human approval for: medium and high risk actions ALWAYS.

Respond ONLY with raw JSON. No markdown, no code blocks, no extra text.
{
  "description": "one sentence description of the fix",
  "commands": ["command1", "command2"],
  "risk_level": "low|medium|high",
  "rollback_commands": ["rollback1", "rollback2"],
  "requires_approval": true
}"""

def clean_json(raw: str) -> str:
    """Strip markdown code blocks if Claude wraps response in them."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    return raw

def remediate(incident_id: str, hypothesis: Hypothesis, device: str) -> RemediationAction:
    """
    Node 3: REMEDIATE
    Based on hypothesis, Claude generates the fix commands + risk score.
    """
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Generate a remediation plan for this diagnosed network incident:

Device: {device}
Root Cause: {hypothesis.cause}
Confidence: {hypothesis.confidence * 100:.0f}%
Evidence:
{chr(10).join(f'  - {e}' for e in hypothesis.evidence)}

Reasoning: {hypothesis.reasoning}

Respond ONLY with raw JSON. No markdown, no code blocks."""
            }
        ]
    )

    raw_response = message.content[0].text
    cleaned = clean_json(raw_response)

    data = json.loads(cleaned)

    return RemediationAction(
        action_id=f"ACT-{str(uuid.uuid4())[:8].upper()}",
        description=data["description"],
        commands=data["commands"],
        risk_level=RiskLevel(data["risk_level"]),
        rollback_commands=data["rollback_commands"],
        requires_approval=data["requires_approval"]
    )


if __name__ == "__main__":
    from nodes.observe import observe_incident
    from nodes.hypothesize import hypothesize

    incident, summary = observe_incident("incidents/bgp_down.json")
    hypothesis = hypothesize(summary)
    remediation = remediate(incident.incident_id, hypothesis, incident.device)

    print("=== REMEDIATION PLAN ===")
    print(f"Action ID  : {remediation.action_id}")
    print(f"Description: {remediation.description}")
    print(f"Risk Level : {remediation.risk_level.upper()}")
    print(f"Needs Approval: {remediation.requires_approval}")
    print(f"\nCommands to execute:")
    for cmd in remediation.commands:
        print(f"  $ {cmd}")
    print(f"\nRollback commands:")
    for cmd in remediation.rollback_commands:
        print(f"  $ {cmd}")