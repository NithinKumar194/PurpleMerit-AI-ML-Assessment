# ── README.md ──────────────────────────────────────────────────

# War Room Multi-Agent System
### Purple Merit Technologies — AI/ML Engineer Assessment 1

A multi-agent system that simulates a cross-functional **product launch war room**,
analyses a mock dashboard (metrics + user feedback), and produces a structured
launch decision: **PROCEED / PAUSE / ROLL_BACK** with a full action plan.

---

## System Architecture

```
Inputs (data/)
  └── metrics.json + feedback.json + release_notes.md
          │
          ▼
  Orchestrator (orchestrator.py)
          │
  ┌───────┼──────────────────────────────────────┐
  │       │                                      │
  ▼       ▼          ▼           ▼               ▼
Data    Product   Marketing    SRE/          Risk/Critic
Analyst Manager   /Comms      Reliability    Agent
Agent   Agent     Agent        Agent (Bonus)
  │       │          │           │               │
  └───────┴──────────┴───────────┴───────────────┘
                    │
                    ▼
          Orchestrator Synthesis
                    │
                    ▼
          output/final_decision.json
```

## Agent Responsibilities

| Agent | Role | Tools Used |
|---|---|---|
| Data Analyst | Quantitative metrics, trends, anomalies | aggregate_metrics, detect_anomalies, compare_to_baseline |
| Product Manager | Success criteria, go/no-go framing | (reads analyst output) |
| Marketing/Comms | Sentiment, perception, comms plan | summarize_sentiment, extract_themes |
| SRE/Reliability | SLA compliance, infrastructure risk | detect_anomalies |
| Risk/Critic | Challenge assumptions, risk register | (reads all outputs) |
| Orchestrator | Final synthesis and decision | (synthesizes all) |

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/war-room-agent.git
cd war-room-agent
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 5. Verify your .env file contains:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## How to Run

```bash
python main.py
```

That's it. The system will:
1. Load all mock data from `data/`
2. Run all 5 agents in sequence
3. Synthesize the final decision
4. Print a summary to console
5. Save full JSON to `output/final_decision.json`

---

## Environment Variables Required

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | YES |

---

## Output Files

| File | Description |
|---|---|
| `output/final_decision.json` | Canonical final output (overwritten each run) |
| `output/final_decision_TIMESTAMP.json` | Timestamped copy per run |
| `logs/run_trace_TIMESTAMP.log` | Full agent trace with tool calls |

---

## Trace Logs — How to Read Them

Logs are in `logs/run_trace_TIMESTAMP.log`

Each line follows this format:
```
TIMESTAMP | war_room.MODULE | MESSAGE
```

Key log patterns:
- `[ORCHESTRATOR] → Dispatching:` — agent being activated
- `[AGENT: Name] → Invoking Tool:` — programmatic tool call happening
- `[TOOL CALL] tool_name() invoked` — inside the tool
- `[TOOL RESULT] tool_name()` — tool output summary
- `[AGENT: Name] LLM response received` — LLM call completed
- `[ORCHESTRATOR] ✓ FINAL DECISION:` — final output ready

---

## Final Output Structure (JSON)

```json
{
  "decision": "ROLL_BACK | PAUSE | PROCEED",
  "rationale": {
    "summary": "...",
    "key_drivers": [...],
    "metric_references": [...],
    "feedback_summary": "..."
  },
  "risk_register": [
    {"risk": "...", "severity": "CRITICAL", "mitigation": "...", "owner": "..."}
  ],
  "action_plan": [
    {"priority": 1, "action": "...", "owner": "...", "deadline": "...", "success_criteria": "..."}
  ],
  "communication_plan": {
    "internal": {"audience": "...", "message": "...", "channel": "...", "timing": "..."},
    "external": {"audience": "...", "message": "...", "channel": "...", "timing": "..."}
  },
  "confidence_score": {
    "score": 87,
    "rating": "HIGH",
    "what_would_increase_confidence": [...]
  },
  "agent_votes": {...},
  "metadata": {...}
}
```

---

## Tech Stack

- Python 3.11+
- anthropic SDK (claude-opus-4-20250514)
- python-dotenv
- No external orchestration framework — custom orchestrator

---

# ── requirements.txt ───────────────────────────────────────────

# requirements.txt
anthropic>=0.25.0
python-dotenv>=1.0.0

---

# ── .env.example ───────────────────────────────────────────────

# .env.example
# Copy this file to .env and fill in your key
ANTHROPIC_API_KEY=sk-ant-your-key-here