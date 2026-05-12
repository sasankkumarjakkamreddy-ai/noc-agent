import os
import json
import anthropic
from models import Hypothesis

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert L3 Network Engineer with 13+ years of experience 
in BGP, MPLS, and enterprise network operations. You reason like a senior escalation 
authority — methodical, evidence-based, and precise.

When given a network incident observation, you:
1. Identify the most likely root cause based on the evidence
2. List specific evidence that supports your hypothesis
3. Assign a confidence score (0.0 to 1.0)
4. Explain your reasoning step by step

You ALWAYS respond in valid JSON matching this exact schema:
{
  "cause": "one sentence root cause",
  "confidence": 0.0 to 1.0,
  "evidence": ["evidence point 1", "evidence point 2", ...],
  "reasoning": "step by step explanation of how you arrived at this conclusion"
}"""

def hypothesize(observation_summary: str) -> Hypothesis:
    """
    Node 2: HYPOTHESIZE
    Send observation to Claude. Get structured root cause hypothesis.
    """
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"""Analyse this network incident and provide your root cause hypothesis:

{observation_summary}

Respond only with the JSON schema specified. No additional text."""
            }
        ]
    )

    raw_response = message.content[0].text.strip()
    if raw_response.startswith("```"):
        raw_response = raw_response.split("```", 2)[1]
        if raw_response.startswith("json"):
            raw_response = raw_response[4:]
        raw_response = raw_response.strip()

    data = json.loads(raw_response)

    hypothesis = Hypothesis(
        cause=data["cause"],
        confidence=float(data["confidence"]),
        evidence=data["evidence"],
        reasoning=data["reasoning"]
    )

    return hypothesis


if __name__ == "__main__":
    from nodes.observe import observe_incident

    incident, summary = observe_incident("incidents/bgp_down.json")
    print("=== OBSERVATION ===")
    print(summary)
    print("\n=== CLAUDE'S HYPOTHESIS ===")
    hypothesis = hypothesize(summary)
    print(f"Root Cause : {hypothesis.cause}")
    print(f"Confidence : {hypothesis.confidence * 100:.0f}%")
    print(f"\nEvidence:")
    for e in hypothesis.evidence:
        print(f"  • {e}")
    print(f"\nReasoning:\n{hypothesis.reasoning}")