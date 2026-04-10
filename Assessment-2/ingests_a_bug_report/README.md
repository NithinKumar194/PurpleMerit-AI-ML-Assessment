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
| Log Analyst Agent | Searches logs for stack traces, error signatures, red herrings |
| Reproduction Agent | Generates and runs a standalone minimal repro script (no server required) |
| Fix Planner Agent | Proposes root-cause hypothesis and patch plan |
| Reviewer/Critic Agent | Challenges assumptions, verifies fix plan, suggests edge cases |

---

## Input Mode
**Option A — Mini Repo** (as recommended by assessment)

The `mini_repo/` folder contains:
- `app.py` — Python module with an intentionally introduced bug: `ZeroDivisionError` in `calculate_discounted_prices()` when `discount_percent = 1.0`
- `bug_report.md` — Full bug report with expected vs actual behavior
- `logs.txt` — Application logs with stack trace and red-herring lines

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/NithinKumar194/PurpleMerit-AI-ML-Assessment
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

--- Starting Agent Orchestration ---

[Triage Agent] Analyzing bug report...
 -> Triage severity assessment: High

[Log Analyst Agent] Parsing logs and correlating with triage data...
 -> Log analysis flagged surface: mini_repo/app.py, line 12, calculate_discounted_prices

[Reproduction Agent] Writing minimal repro script...
[*] Tool Execution: Running generated script (repro.py)...
 -> Reproduction execution successful: Triggered ZeroDivisionError as expected.

[Fix Planner Agent] Proposing root cause and patch...
 -> Root Cause Hypothesis: formula `price / (1 - discount)` should be `price * (1 - discount)` (Confidence: High)

[Reviewer Agent] Critiquing fix plan...
 -> Review approved: True

Final structured report generated at resolution_output.json.
✅  Fix plan APPROVED by Reviewer. Ready for implementation.
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
| `repro.py` | Minimal standalone script that reproduces the bug (no server needed) |
| `resolution_output.json` | Full structured output — root cause, patch plan, validation |

---

## Structured Output (`resolution_output.json`) Contains

- `bug_summary` — symptoms, scope, severity
- `evidence` — log lines, stack trace excerpts, red herrings identified
- `repro_steps_and_artifact` — how to run repro.py + expected failing output
- `root_cause_hypothesis` — with confidence score
- `patch_plan` — files impacted, approach, risks
- `validation_plan` — tests to add, regression checks
- `open_questions` — missing info / follow-up items
- `agent_traces_and_feedback` — reviewer approval + critique

---
## Trace Logs

All agent decisions and tool calls are printed to the console during execution.

### How to read the trace
Each line is prefixed with the agent name:

## Trace Logs

All agent decisions and tool calls are printed to the console during execution.
Each step is clearly labelled:
```
[Triage Agent] Analyzing bug report...
[Log Analyst Agent] Parsing logs and correlating with triage data...
[Reproduction Agent] Writing minimal repro script...
[*] Tool Execution: Running generated script (repro.py)...
[Fix Planner Agent] Proposing root cause and patch...
[Reviewer Agent] Critiquing fix plan...
```
Console output = the trace. No separate log file is written.

---

## Tech Stack

- Python 3.9+
- OpenAI GPT-4o-mini (structured outputs via Pydantic)
- python-dotenv
- subprocess (tool execution for repro script)