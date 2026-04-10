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
        "and triggers the exact error WITHOUT starting any server or making any HTTP request."
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
                        "You are a Reproduction Agent. Your ONLY job is to write a minimal "
                        "standalone Python script that reproduces the bug by calling the faulty "
                        "function directly.\n\n"
                        "STRICT RULES — violating any of these will cause the test to fail:\n"
                        "1. Do NOT import or use Flask, requests, httpx, urllib, aiohttp, "
                        "   or ANY HTTP/network library.\n"
                        "2. Do NOT start a server, subprocess, or any background process.\n"
                        "3. Import the function under test as: "
                        "   `from mini_repo.app import calculate_discounted_prices`\n"
                        "4. Call the function with the exact input that triggers the error.\n"
                        "5. The script MUST exit with code 1 when the bug is present.\n"
                        "6. Print 'BUG REPRODUCED' before re-raising the exception.\n"
                        "7. Keep the script under 30 lines."
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
    ) -> FixPlan:
        print("\n[Fix Planner Agent] Proposing root cause and patch...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Fix Planner Agent. Propose the root cause and a minimal, "
                        "safe patch based on the reproduction output and log evidence."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Codebase:\n{json.dumps(codebase)}\n\n"
                        f"Logs:\n{log_data.model_dump_json()}\n\n"
                        f"Reproduction Output:\n{repro_output}"
                    ),
                },
            ],
            response_format=FixPlan,
        )
        return completion.choices[0].message.parsed

    def review_plan(self, fix_plan: FixPlan, repro_output: str) -> ReviewerOutput:
        print("\n[Reviewer Agent] Critiquing fix plan...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Reviewer/Critic Agent. Challenge weak assumptions, "
                        "verify the repro is truly minimal and matches the bug, confirm "
                        "the fix is safe and complete, and suggest edge cases."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Fix Plan:\n{fix_plan.model_dump_json()}\n\n"
                        f"Repro Output:\n{repro_output}"
                    ),
                },
            ],
            response_format=ReviewerOutput,
        )
        return completion.choices[0].message.parsed