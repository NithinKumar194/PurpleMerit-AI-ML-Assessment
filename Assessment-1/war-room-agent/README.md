# Assessment 2 — Bug Resolution Multi-Agent System
### Purple Merit Technologies — AI/ML Engineer Assessment

An automated multi-agent system that ingests a bug report and related logs,
reproduces the issue by generating a minimal reproducible script, and outputs
a root-cause hypothesis plus a patch plan.

---

## System Architecture

```
Inputs (mini_repo/)
  └── bug_report.md + logs.txt + app.py
          │
          ▼
  Orchestrator (main.py)
          │
  ┌───────┼──────────────────────────────────────┐
  │       │              │           │            │
  ▼       ▼              ▼           ▼            ▼
Triage  Log Analyst  Reproduction  Fix Planner  Reviewer
Agent   Agent        Agent         Agent        /Critic
  │       │              │           │            │
  └───────┴──────────────┴───────────┴────────────┘
                    │
                    ▼
          resolution_output.json
          repro.py (runnable artifact)
```

---

## Agent Responsibilities

| Agent | Role |
|---|---|
| Triage Agent | Extracts symptoms, expected vs actual behavior, prioritizes hypotheses |
| Log Analyst Agent | Searches logs for stack traces, error signatures, anomalies |
| Reproduction Agent | Generates and runs minimal reproduction script (repro.py) |
| Fix Planner Agent | Proposes root-cause hypothesis and patch plan |
| Reviewer/Critic Agent | Challenges assumptions, verifies fix plan, suggests edge cases |

---

## Input Mode
**Option A — Mini Repo** (as recommended by assessment)

The `mini_repo/` folder contains:
- `app.py` — Flask app with an intentionally introduced bug (KeyError on missing 'price' field)
- `bug_report.md` — Full bug report with expected vs actual behavior
- `logs.txt` — Application logs with stack traces and red herring lines

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/NithinKumar194/PurpleMerit-AI-ML-Assessment/tree/main/Assessment-2/ingests_a_bug_report
cd PurpleMerit-AI-ML-Assessment/Assessment-2/ingests_a_bug_report
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variable
Create a `.env` file in this folder:
```
OPENAI_API_KEY=sk-your-openai-key-here
```

---

## How to Run

```bash
python main.py
```

---

## Example Output

```
Loading inputs (bug report, logs, codebase)...
Running Triage Agent...
Running Log Analyst Agent...
Running Reproduction Agent...
Executing repro.py...
Running Fix Planner Agent...
Running Reviewer Agent...
resolution_output.json written.
```

---

## Environment Variables Required

| Variable | Description | Required |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | YES |

---

## Output Files Generated

| File | Description |
|---|---|
| `repro.py` | Minimal runnable script that reproduces the bug consistently |
| `resolution_output.json` | Full structured output — root cause, patch plan, validation |

---

## Structured Output (resolution_output.json) Contains

- Bug summary (symptoms, scope, severity)
- Evidence (log lines, stack trace excerpts)
- Repro steps + repro artifact path
- Root-cause hypothesis (with confidence score)
- Patch plan (files impacted, approach, risks)
- Validation plan (tests to add, regression checks)
- Open questions / missing info

---

## Trace Logs

All agent decisions and tool calls are printed to console during execution.
Each agent step is clearly labeled:
```
[TRIAGE AGENT] Starting...
[LOG ANALYST AGENT] Searching logs...
[REPRODUCTION AGENT] Generating repro script...
[TOOL] Executing repro.py via subprocess...
[FIX PLANNER AGENT] Proposing patch...
[REVIEWER AGENT] Critiquing plan...
```

---

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o
- Flask (mini_repo app)
- python-dotenv
- subprocess (tool execution)