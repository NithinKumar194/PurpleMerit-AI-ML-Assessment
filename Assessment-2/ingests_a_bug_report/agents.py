import json
from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI

# Schemas modeled exactly after the assessment's "Structured outputs" requirements

class TriageOutput(BaseModel):
    summary: str = Field(description="Summary of the bug, including scope and core symptoms")
    severity: str = Field(description="Estimated severity of the bug (e.g., Low, Medium, High, Critical)")
    environment_details: str = Field(description="Details regarding the environment (OS, Language version, etc.)")
    expected_behavior: str = Field(description="Expected behavior based on the report")
    actual_behavior: str = Field(description="Actual observed behavior")
    prioritized_hypotheses: List[str] = Field(description="List of initial root cause hypotheses prioritized by likelihood")

class LogAnalysisOutput(BaseModel):
    stack_traces: List[str] = Field(description="Extracted relevant stack traces or error signatures")
    failure_surface: str = Field(description="Most likely file and line number / functional area")
    anomalies: List[str] = Field(description="Any other key anomalies found in logs (or red herrings)")

class ReproductionScript(BaseModel):
    script_content: str = Field(description="A fully runnable Python script that imports the faulty code and triggers the exact error.")
    execution_command: str = Field(description="The command used to run this script (e.g., python repro.py)")

class FixPlan(BaseModel):
    root_cause_hypothesis: str = Field(description="The determined root cause based on logs and reproduction")
    confidence: str = Field(description="Confidence level in the root-cause hypothesis (e.g., High, Medium, Low)")
    patch_approach: str = Field(description="Step by step approach to fix the bug")
    files_impacted: List[str] = Field(description="List of files to modify")
    risks: List[str] = Field(description="Potential risks associated with this patch")
    validation_plan: str = Field(description="Tests to add or regression checks to perform")
    open_questions: List[str] = Field(description="Any open questions or missing info required to fully resolve it")

class ReviewerOutput(BaseModel):
    is_approved: bool = Field(description="Whether the fix plan is safe and addresses the root cause")
    feedback: str = Field(description="Feedback, edge cases, and weak assumptions. Why it was approved or rejected.")
    
# Agent implementations
class AgentOrchestrator:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini" # Fast, cheap, and supports structured output natively

    def run_triage(self, bug_report: str) -> TriageOutput:
        print("\n[Triage Agent] Analyzing bug report...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Triage Agent. Extract key symptoms, scope, severity, behavior, environment details, and prioritize hypotheses."},
                {"role": "user", "content": bug_report}
            ],
            response_format=TriageOutput,
        )
        return completion.choices[0].message.parsed
        
    def run_log_analyst(self, logs: str, triage_data: TriageOutput) -> LogAnalysisOutput:
        print("\n[Log Analyst Agent] Parsing logs and correlating with triage data...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Log Analyst Agent. Search logs for stack traces, error signatures, and key anomalies. Ignore red herrings."},
                {"role": "user", "content": f"Logs:\n{logs}\n\nTriage Data:\n{triage_data.model_dump_json()}"}
            ],
            response_format=LogAnalysisOutput,
        )
        return completion.choices[0].message.parsed

    def generate_reproduction(self, codebase: dict, triage_data: TriageOutput, log_data: LogAnalysisOutput) -> ReproductionScript:
        print("\n[Reproduction Agent] Writing minimal repro script...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Reproduction Agent. Construct a minimal python test script that triggers the failure in the simplest way. Because you run from the project root, import as `from mini_repo.app import calculate_discounted_prices`."},
                {"role": "user", "content": f"Codebase:\n{json.dumps(codebase)}\n\nTriage:\n{triage_data.model_dump_json()}\n\nLogs:\n{log_data.model_dump_json()}"}
            ],
            response_format=ReproductionScript,
        )
        return completion.choices[0].message.parsed

    def plan_fix(self, codebase: dict, log_data: LogAnalysisOutput, repro_output: str) -> FixPlan:
        print("\n[Fix Planner Agent] Proposing root cause and patch...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Fix Planner Agent. Propose root-cause and patch approach based on the exact output of the reproduction test and previously analyzed logs."},
                {"role": "user", "content": f"Codebase:\n{json.dumps(codebase)}\n\nLogs:\n{log_data.model_dump_json()}\n\nReproduction Output:\n{repro_output}"}
            ],
            response_format=FixPlan,
        )
        return completion.choices[0].message.parsed

    def review_plan(self, fix_plan: FixPlan, repro_output: str) -> ReviewerOutput:
        print("\n[Reviewer Agent] Critiquing fix plan...")
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Reviewer/Critic Agent. Challenge assumptions, check if the repro is minimal, verify the fix is safe, and suggest edge cases."},
                {"role": "user", "content": f"Fix Plan:\n{fix_plan.model_dump_json()}\n\nRepro Output:\n{repro_output}"}
            ],
            response_format=ReviewerOutput,
        )
        return completion.choices[0].message.parsed
