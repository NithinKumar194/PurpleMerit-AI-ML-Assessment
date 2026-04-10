import os
import json
import subprocess
from dotenv import load_dotenv
from agents import AgentOrchestrator

def load_file(path):
    with open(path, 'r') as f:
        return f.read()

def run_script_tool(script_content: str, script_path: str = "repro.py") -> str:
    """Executes the given python script and returns the output. This satisfies programmatic Tool Calling Requirements."""
    with open(script_path, "w") as f:
        f.write(script_content)
    
    print(f"[*] Tool Execution: Running generated script ({script_path})...")
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    
    output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
    return output

def main():
    # Attempt to load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY in a .env file located in this directory.")
        return

    orchestrator = AgentOrchestrator(api_key=api_key)
    
    # 1. Parse inputs
    print("Loading inputs (bug report, logs, codebase)...")
    bug_report = load_file("mini_repo/bug_report.md")
    logs = load_file("mini_repo/logs.txt")
    app_code = load_file("mini_repo/app.py")
    codebase = {"mini_repo/app.py": app_code}
    
    print("\n--- Starting Agent Orchestration ---")
    
    # 2. Triage
    triage_result = orchestrator.run_triage(bug_report)
    print(f" -> Triage severity assessment: {triage_result.severity}")
    
    # 3. Log Analysis
    log_result = orchestrator.run_log_analyst(logs, triage_result)
    print(f" -> Log analysis flagged surface: {log_result.failure_surface}")
    
    # 4. Reproduction
    repro_script = orchestrator.generate_reproduction(codebase, triage_result, log_result)
    
    # Run the script (Tool Execution Requirement)
    obs_output = run_script_tool(repro_script.script_content, "repro.py")
    if "ZeroDivisionError" in obs_output:
         print(" -> Reproduction execution successful: Triggered ZeroDivisionError as expected.")
    else:
         print(" -> Reproduction execution output unexpected. Logging output...")
         
    # 5. Fix Planning
    fix_plan = orchestrator.plan_fix(codebase, log_result, obs_output)
    print(f" -> Root Cause Hypothesis: {fix_plan.root_cause_hypothesis} (Confidence: {fix_plan.confidence})")
    
    # 6. Review
    review_result = orchestrator.review_plan(fix_plan, obs_output)
    print(f" -> Review approved: {review_result.is_approved}")
    if not review_result.is_approved:
        print(f" -> Critic feedback: {review_result.feedback}")
    
    # 7. Generate Structured Output explicitly mapping to required fields
    final_report = {
        "bug_summary": triage_result.model_dump(),
        "evidence": log_result.model_dump(),
        "repro_steps_and_artifact": {
            "repro_artifact_path": "repro.py",
            "execution_command": repro_script.execution_command
        },
        "root_cause_hypothesis": {
            "hypothesis": fix_plan.root_cause_hypothesis,
            "confidence": fix_plan.confidence
        },
        "patch_plan": {
            "approach": fix_plan.patch_approach,
            "files_impacted": fix_plan.files_impacted,
            "risks": fix_plan.risks
        },
        "validation_plan": fix_plan.validation_plan,
        "open_questions": fix_plan.open_questions,
        "agent_traces_and_feedback": review_result.model_dump()
    }
    
    out_file = "resolution_output.json"
    with open(out_file, "w") as f:
        json.dump(final_report, f, indent=4)
        
    print(f"\nFinal structured report generated at {out_file}.")

if __name__ == "__main__":
    main()
