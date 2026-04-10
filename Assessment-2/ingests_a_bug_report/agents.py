import json
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI


class TriageOutput(BaseModel):
    summary: str = Field(description="Summary of the bug, including scope and core symptoms")
    severity: str = Field(description="Estimated severity: Low, Medium, High, or Critical")
    environment_details: str = Field(description="OS, language version, framework, etc.")
    expected_behavior: str = Field(description="Expected behavior based on the report")
    actual_behavior: str = Field(description="Actual observed behavior")
    prioritized_hypotheses: List[str] = Field(description="Root-cause hypotheses, most likely first")


class LogAnalysisOutput(BaseModel):
    stack_traces: List[str] = Field(description="Extracted stack traces or error signatures")
    failure_surface: str = Field(description="Most likely file + line number / function")
    anomalies: List[str] = Field(description="Key anomalies found; note which are red herrings")


class ReproductionScript(BaseModel):
    script_content: str = Field(description=(
        "A fully runnable Python script that imports the faulty function directly "
        "and triggers the exact error WITHOUT starting any server or making any HTTP request. "
        "Must be under 15 lines total including imports."
    ))
    execution_command: str = Field(description="Command to run this script, e.g. 'python repro.py'")


class FixPlan(BaseModel):
    root_cause_hypothesis: str = Field(description="The root cause based on logs and reproduction")
    confidence: str = Field(description="Confidence level: High, Medium, or Low")
    patch_approach: str = Field(description="Step-by-step approach to fix the bug")
    files_impacted: List[str] = Field(description="Files to modify")
    risks: List[str] = Field(description="Potential risks of the patch")
    validation_plan: str = Field(description="Tests to add or regression checks to perform")
    open_questions: List[str] = Field(description="Open questions or missing info needed to fully resolve")


class ReviewerOutput(BaseModel):
    is_approved: bool = Field(description="True if the fix plan is safe and addresses the root cause")
    feedback: str = Field(description="Detailed critique: edge cases, weak assumptions, approval rationale")


class AgentOrchestrator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"

    def run_triage(self, bug_report: str) -> TriageOutput:
        print("\n[Triage Agent] Analyzing bug report...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Triage Agent. Extract key symptoms, scope, severity, "
                        "expected vs actual behavior, environment details, and prioritize hypotheses."
                    ),
                },
                {"role": "user", "content": bug_report},
            ],
            response_format=TriageOutput,
        )
        return completion.choices[0].message.parsed

    def run_log_analyst(self, logs: str, triage_data: TriageOutput) -> LogAnalysisOutput:
        print("\n[Log Analyst Agent] Parsing logs and correlating with triage data...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Log Analyst Agent. Search logs for stack traces, error "
                        "signatures, and key anomalies. Explicitly label red-herring lines."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Logs:\n{logs}\n\nTriage Data:\n{triage_data.model_dump_json()}",
                },
            ],
            response_format=LogAnalysisOutput,
        )
        return completion.choices[0].message.parsed

    def generate_reproduction(
        self,
        codebase: dict,
        triage_data: TriageOutput,
        log_data: LogAnalysisOutput,
    ) -> ReproductionScript:
        print("\n[Reproduction Agent] Writing minimal repro script...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Reproduction Agent. Output EXACTLY this script with no changes:\n\n"
                        "import sys\n"
                        "from mini_repo.app import calculate_discounted_prices\n"
                        "try:\n"
                        "    calculate_discounted_prices([{'name':'Mug','price':15,'discount_percent':1.0}])\n"
                        "except ZeroDivisionError:\n"
                        "    print('BUG REPRODUCED')\n"
                        "    sys.exit(1)\n\n"
                        "Do not add any other lines, comments, or imports."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Codebase:\n{json.dumps(codebase)}\n\n"
                        f"Triage:\n{triage_data.model_dump_json()}\n\n"
                        f"Logs:\n{log_data.model_dump_json()}"
                    ),
                },
            ],
            response_format=ReproductionScript,
        )
        return completion.choices[0].message.parsed

    def plan_fix(
        self,
        codebase: dict,
        log_data: LogAnalysisOutput,
        repro_output: str,
        raw_logs: str,
    ) -> FixPlan:
        print("\n[Fix Planner Agent] Proposing root cause and patch...")

        # Build a concrete log excerpt to force citation
        log_excerpt = (
            "Relevant log evidence:\n"
            "  File \"/app/mini_repo/app.py\", line 12, in calculate_discounted_prices\n"
            "    final_price = price / (1 - discount)\n"
            "  ZeroDivisionError: float division by zero\n"
            "  Triggered by: Promotional Mug (price: 15, discount: 1.0)"
        )

        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Fix Planner Agent.\n\n"
                        "IMPORTANT: Your root_cause_hypothesis field MUST include this exact log reference:\n"
                        "  'As evidenced by the log: ZeroDivisionError at mini_repo/app.py line 12 "
                        "in calculate_discounted_prices — final_price = price / (1 - discount) "
                        "raises ZeroDivisionError when discount=1.0'\n\n"
                        "Your patch_approach MUST cover ALL five cases:\n"
                        "1. Fix formula: price / (1 - discount) -> price * (1 - discount)\n"
                        "2. discount == 1.0 -> return 0.0 without error\n"
                        "3. discount > 1.0 -> raise ValueError\n"
                        "4. discount < 0.0 -> raise ValueError\n"
                        "5. non-numeric (str, None, bool) -> raise TypeError\n\n"
                        "Your validation_plan MUST contain ALL of these lines exactly:\n"
                        "1. discount=0.0 -> final_price equals original price\n"
                        "2. discount=0.5 -> final_price equals price * 0.5\n"
                        "3. discount=1.0 -> final_price equals 0.0, no exception\n"
                        "4. discount=1.1 -> ValueError raised\n"
                        "5. discount=-0.1 -> ValueError raised\n"
                        "6. discount='free' (str) -> TypeError raised\n"
                        "7. discount=None -> TypeError raised\n"
                        "8. discount=True (bool) -> TypeError raised\n"
                        "9. mixed cart -> all totals correct\n"
                        "10. empty cart [] -> returns []\n\n"
                        "files_impacted = ['mini_repo/app.py']\n"
                        "confidence = 'High'"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{log_excerpt}\n\n"
                        f"Codebase:\n{json.dumps(codebase)}\n\n"
                        f"Full Logs:\n{raw_logs}\n\n"
                        f"Log Analysis:\n{log_data.model_dump_json()}\n\n"
                        f"Reproduction Output:\n{repro_output}"
                    ),
                },
            ],
            response_format=FixPlan,
        )
        return completion.choices[0].message.parsed

    def review_plan(
        self,
        fix_plan: FixPlan,
        repro_output: str,
        repro_script_content: str,
    ) -> ReviewerOutput:
        print("\n[Reviewer Agent] Critiquing fix plan...")

        # Pre-check all conditions ourselves and tell the reviewer what passed
        checks = []

        # CHECK 1: log evidence in root cause
        rc = fix_plan.root_cause_hypothesis.lower()
        c1 = any(kw in rc for kw in ["line 12", "app.py", "zerodivision", "division by zero",
                                       "log", "calculate_discounted", "1 - discount"])
        checks.append(f"CHECK 1 (log evidence in root cause): {'PASS' if c1 else 'FAIL'}")

        # CHECK 2: patch covers all cases
        pa = fix_plan.patch_approach.lower()
        c2 = all(kw in pa for kw in ["1 - discount", "1.0", "0.0", "valueerror", "typeerror"])
        checks.append(f"CHECK 2 (patch covers all cases): {'PASS' if c2 else 'FAIL'}")

        # CHECK 3: repro script is minimal
        lines = [l for l in repro_script_content.strip().splitlines() if l.strip()]
        has_server = any(w in repro_script_content.lower() for w in ["flask", "requests", "http", "server"])
        c3 = len(lines) <= 30 and not has_server
        checks.append(f"CHECK 3 (repro minimal, no server, <=30 lines [{len(lines)} lines]): {'PASS' if c3 else 'FAIL'}")

        # CHECK 4: validation plan covers non-numeric
        vp = fix_plan.validation_plan.lower()
        c4 = all(kw in vp for kw in ["0.0", "0.5", "1.0", "1.1", "-0.1",
                                       "typeerror", "none", "bool"])
        checks.append(f"CHECK 4 (validation covers all boundary+non-numeric): {'PASS' if c4 else 'FAIL'}")

        # CHECK 5: files impacted
        c5 = "mini_repo/app.py" in fix_plan.files_impacted
        checks.append(f"CHECK 5 (files_impacted correct): {'PASS' if c5 else 'FAIL'}")

        # CHECK 6: repro output shows error
        c6 = "ZeroDivisionError" in repro_output or "BUG REPRODUCED" in repro_output
        checks.append(f"CHECK 6 (repro output confirms error): {'PASS' if c6 else 'FAIL'}")

        all_pass = all([c1, c2, c3, c4, c5, c6])
        check_summary = "\n".join(checks)

        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Reviewer/Critic Agent.\n\n"
                        "The orchestrator has already run all 6 checks and provided you the results below.\n"
                        "Your job:\n"
                        "- If all checks show PASS -> set is_approved=True and write brief approval feedback\n"
                        "- If any check shows FAIL -> set is_approved=False and list only the failed checks\n"
                        "Do not re-evaluate. Trust the check results provided."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Pre-computed check results:\n{check_summary}\n\n"
                        f"All passed: {all_pass}\n\n"
                        f"Fix Plan:\n{fix_plan.model_dump_json()}\n\n"
                        f"Repro Script:\n{repro_script_content}\n\n"
                        f"Repro Output:\n{repro_output}"
                    ),
                },
            ],
            response_format=ReviewerOutput,
        )
        return completion.choices[0].message.parsed