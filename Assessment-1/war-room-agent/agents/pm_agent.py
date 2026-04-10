import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger("war_room.agents.pm")

PM_SYSTEM = """You are the Product Manager in a product launch war room.
You defined the success criteria before launch. Your job now is to:
- Evaluate each success criterion: PASS or FAIL with the actual vs target value
- Assess user impact and business impact in concrete terms
- Frame the go/no-go decision from a product strategy perspective
- Consider rollback cost and complexity based on the release notes

Respond ONLY in valid JSON with exactly these keys:
{
  "success_criteria_assessment": "overall pass/fail summary string",
  "criteria_pass_fail": [
    {"criterion": "...", "target": "...", "actual": "...", "status": "PASS|FAIL"}
  ],
  "user_impact_assessment": "string",
  "business_impact": "string",
  "go_nogo_framing": "string explaining the PM perspective",
  "preliminary_recommendation": "PROCEED|PAUSE|ROLL_BACK"
}"""


class PMAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Product Manager Agent",
            role_description="Defines success criteria, user impact, and go/no-go framing"
        )

    def analyze(self, release_notes: str, analyst_output: dict) -> dict:
        logger.info(f"[AGENT: {self.name}] ── Starting Analysis ──")

        user_msg = f"""
RELEASE NOTES AND PRE-DEFINED SUCCESS CRITERIA:
{release_notes}

DATA ANALYST FINDINGS (from previous agent):
{json.dumps({k: v for k, v in analyst_output.items() if not k.startswith('_')}, indent=2)}

Based on the defined success criteria and analyst findings, provide your PM assessment in JSON.
"""
        raw = self.call_llm(PM_SYSTEM, user_msg)
        result = self.parse_json_response(raw)
        logger.info(
            f"[AGENT: {self.name}] ✓ Complete | "
            f"Recommendation: {result.get('preliminary_recommendation')}"
        )
        return result