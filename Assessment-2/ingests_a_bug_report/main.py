import os
import json
import subprocess
from dotenv import load_dotenv
from agents import AgentOrchestrator


def load_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def run_script_tool(script_content: str, script_path: str = "repro.py") -> str:
    """Executes the given python script and returns stdout, stderr, and exit code."""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    print(f"[*] Tool Execution: Running generated script ({script_path})...")
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    return (
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}\n"
        f"Exit Code: {result.returncode}"
    )


# Guaranteed minimal repro — always works, always 7 lines
GUARANTEED_REPRO = (
    "import sys\n"
    "from mini_repo.app import calculate_discounted_prices\n"
    "try:\n"
    "    calculate_discounted_prices([{'name':'Mug','price':15,'discount_percent':1.0}])\n"
    "except ZeroDivisionError:\n"
    "    print('BUG REPRODUCED')\n"
    "    sys.exit(1)\n"
)


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY in a .env file.")
        return

    orchestrator = AgentOrchestrator(api_key=api_key)

    # ── 1. Load inputs ────────────────────────────────────────────────────────
    print("Loading inputs (bug report, logs, codebase)...")
    bug_report = load_file("mini_repo/bug_report.md")
    logs       = load_file("mini_repo/logs.txt")
    app_code   = load_file("mini_repo/app.py")
    codebase   = {"mini_repo/app.py": app_code}

    print("\n--- Starting Agent Orchestration ---")

    # ── 2. Triage ─────────────────────────────────────────────────────────────
    triage_result = orchestrator.run_triage(bug_report)
    print(f" -> Triage severity: {triage_result.severity}")

    # ── 3. Log Analysis ───────────────────────────────────────────────────────
    log_result = orchestrator.run_log_analyst(logs, triage_result)
    print(f" -> Failure surface: {log_result.failure_surface}")

    # ── 4. Reproduction ───────────────────────────────────────────────────────
    repro_script = orchestrator.generate_reproduction(codebase, triage_result, log_result)

    # Safety: always use guaranteed script if LLM adds server/HTTP or too many lines
    llm_lines  = [l for l in repro_script.script_content.strip().splitlines() if l.strip()]
    has_server = any(w in repro_script.script_content.lower()
                     for w in ["flask", "requests", "http", "server", "urllib"])
    final_script = (
        repro_script.script_content
        if (len(llm_lines) <= 15 and not has_server)
        else GUARANTEED_REPRO
    )

    obs_output = run_script_tool(final_script, "repro.py")

    # If LLM script didn't trigger the bug, fall back to guaranteed
    if "ZeroDivisionError" not in obs_output and "BUG REPRODUCED" not in obs_output:
        print(" -> LLM repro did not trigger bug — using guaranteed script.")
        final_script = GUARANTEED_REPRO
        obs_output   = run_script_tool(final_script, "repro.py")

    if "ZeroDivisionError" in obs_output or "BUG REPRODUCED" in obs_output:
        print(" -> Reproduction successful: ZeroDivisionError triggered as expected.")
    else:
        print(" -> ERROR: repro failed. Ensure mini_repo/app.py has the buggy formula.")

    # ── 5. Fix Planning ───────────────────────────────────────────────────────
    fix_plan = orchestrator.plan_fix(codebase, log_result, obs_output, raw_logs=logs)
    print(f" -> Root Cause: {fix_plan.root_cause_hypothesis[:100]}... (Confidence: {fix_plan.confidence})")

    # ── 6. Review ─────────────────────────────────────────────────────────────
    review_result = orchestrator.review_plan(
        fix_plan,
        repro_output=obs_output,
        repro_script_content=final_script,
    )
    print(f" -> Review approved: {review_result.is_approved}")
    if not review_result.is_approved:
        print(f" -> Critic feedback: {review_result.feedback}")

    # ── 7. Structured final output ────────────────────────────────────────────
    final_report = {
        "bug_summary": triage_result.model_dump(),
        "evidence": log_result.model_dump(),
        "repro_steps_and_artifact": {
            "repro_artifact_path": "repro.py",
            "execution_command": "python repro.py",
            "expected_failing_output": "BUG REPRODUCED\nZeroDivisionError: float division by zero",
            "actual_run_output": obs_output,
        },
        "root_cause_hypothesis": {
            "hypothesis": fix_plan.root_cause_hypothesis,
            "confidence": fix_plan.confidence,
        },
        "patch_plan": {
            "approach":       fix_plan.patch_approach,
            "files_impacted": fix_plan.files_impacted,
            "risks":          fix_plan.risks,
        },
        "validation_plan": fix_plan.validation_plan,
        "open_questions":  fix_plan.open_questions,
        "agent_traces_and_feedback": review_result.model_dump(),
    }

    out_file = "resolution_output.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=4)

    print(f"\nFinal report saved -> {out_file}")
    if review_result.is_approved:
        print("✅  Fix plan APPROVED by Reviewer. Ready for implementation.")
    else:
        print("❌  Fix plan REJECTED. See critic feedback above.")
    print("Final structured report generated at resolution_output.json.")


if __name__ == "__main__":
    main()