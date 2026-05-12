# ⚡ NOC Agent — Explainable Agentic Incident Response

An autonomous network operations system that diagnoses BGP incidents, generates remediation plans, and **pauses for human approval** before touching production. Every decision is logged, explainable, and auditable.

Built with **Claude (Anthropic) + LangGraph + FastAPI + React**.

---

## The Problem

71% of IT leaders don't trust AI to make autonomous network changes. The blocker isn't accuracy — it's **auditability**. Most AI tools give you an answer but not the reasoning behind it.

This system shows its work at every step.

---

## How It Works

```
Syslog Alert → OBSERVE → HYPOTHESIZE (Claude) → REMEDIATE (Claude) → HUMAN APPROVAL → Audit Log
```

| Step | What Happens |
|------|-------------|
| 🔍 **OBSERVE** | Parses raw syslog, extracts key signals (interface, peer IP, timestamps) |
| 🧠 **HYPOTHESIZE** | Claude reasons like an L3 engineer — root cause, evidence, confidence % |
| 🔧 **REMEDIATE** | Generates exact IOS XR fix commands + rollback plan, rates risk level |
| ⚠️ **HUMAN APPROVAL** | Blocks execution until a human approves — high-risk changes never auto-execute |
| 📋 **AUDIT TRAIL** | Every incident, hypothesis, action, and approval logged to SQLite |

### Demo Scenario

**Incident:** BGP session down on `core-router-zurich-01`

**Claude's diagnosis:**
- Root cause: MTU mismatch (local=1500, peer=9000)
- Cause: Automated agent changed interface MTU 2 hours prior
- Confidence: 92%
- Risk: MEDIUM → human approval required

**Generated fix commands:**
```
configure terminal
interface TenGigE0/0/0/0
mtu 9000
commit
end
clear bgp ipv4 unicast * soft
```

**Rollback commands ready** if the fix fails.

---

## Project Structure

```
noc-agent/
├── backend/
│   ├── main.py              # FastAPI app, REST endpoints
│   ├── graph.py             # LangGraph agent pipeline
│   ├── models.py            # Pydantic data models
│   ├── db.py                # SQLite audit log
│   ├── nodes/
│   │   ├── observe.py       # Step 1: parse incident
│   │   ├── hypothesize.py   # Step 2: Claude root cause analysis
│   │   ├── remediate.py     # Step 3: Claude remediation plan
│   │   └── validate.py      # Step 4: human approval gate
│   └── incidents/
│       └── bgp_down.json    # Sample BGP incident
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main dashboard UI
│   │   └── main.jsx         # React entry point
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── requirements.txt
└── README.md
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | Claude 3.5 Sonnet (Anthropic) |
| Agent Orchestration | LangGraph |
| Backend API | FastAPI + Uvicorn |
| Database | SQLite (audit log) |
| Frontend | React + Vite + Tailwind CSS |
| HTTP Client | Axios |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
uvicorn main:app --reload --port 8080
```

API running at: `http://localhost:8080`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Dashboard running at: `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/incidents/trigger-async` | Trigger BGP incident (non-blocking) |
| `GET` | `/incidents` | List all incidents from audit log |
| `GET` | `/incidents/{id}` | Get single incident detail |
| `POST` | `/incidents/{id}/approve` | Approve or reject remediation |

---

## Roadmap

- [ ] **Problem 2** — AI readiness scoring for RoCEv2/RDMA network fabrics
- [ ] **Problem 3** — Config validation guardrail with Batfish (pre-execution static analysis)
- [ ] Kafka integration for real-time syslog ingestion
- [ ] Multi-vendor support (Junos, EOS, NX-OS)
- [ ] Slack/Teams alert integration
- [ ] Docker Compose for one-command deployment

---

## Author

**Sasanka Kumar Jakkamreddy** — Technical Support Manager | CCNA | ITIL V4 | Azure 900

Building AI-native network operations tooling.

[LinkedIn](https://www.linkedin.com/in/sasanka-kumar-jakkamreddy-64b00559/) · [GitHub](https://github.com/sasankkumarjakkamreddy-ai/)

---

## License

MIT