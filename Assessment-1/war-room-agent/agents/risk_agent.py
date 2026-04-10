import json
import logging
from agents.base_agent import BaseAgent

logger = logging.getLogger("war_room.agents.risk")

RISK_SYSTEM = """You are the Risk/Critic Agent in a product launch war room.
You are the most skeptical person in the room. Your job is to challenge every assumption.
You must:
- Identify logical gaps or overconfident claims in other agents' analyses
- Enumerate the top risks if rollout CONTINUES (severity + mitigation + owner)
- Enumerate risks if we ROLL BACK (rollback risks)
- VETO any lenient recommendation if you believe it is unsafe — explain exactly why
- Assign a final confidence score (0-100) to the overall decision picture
- List what specific evidence would increase confidence

Respond ONLY in valid JSON with exactly these keys:
{
  "challenged_assumptions": ["assumption1 challenged because...", ...],
  "risk_register": [
    {
      "risk": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "mitigation": "string",
      "owner": "string"
    }
  ],
  "rollback_risks": ["risk1", "risk2"],
  "veto_flag": true|false,
  "veto_reason": "string or null",
  "confidence_score": 0-100,
  "confidence_gaps": ["what evidence would increase confidence", ...]
}"""


class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Risk/Critic Agent",
            role_description="Challenges assumptions, highlights risks, requests additional evidence"
        )

    def analyze(self, analyst_output: dict, pm_output: dict, marketing_output: dict) -> dict:
        logger.info(f"[AGENT: {self.name}] ── Starting Analysis ──")

        # Strip internal tool outputs before sending to LLM to save tokens
        def clean(d):
            return {k: v for k, v in d.items() if not k.startswith('_')}

        user_msg = f"""
You have received assessments from three agents. Challenge them rigorously.

DATA ANALYST ASSESSMENT:
{json.dumps(clean(analyst_output), indent=2)}

PRODUCT MANAGER ASSESSMENT:
{json.dumps(pm_output, indent=2)}

MARKETING/COMMS ASSESSMENT:
{json.dumps(clean(marketing_output), indent=2)}

Challenge all assumptions. Build the complete risk register. Provide your Risk/Critic assessment in JSON.
"""
        raw = self.call_llm(RISK_SYSTEM, user_msg)
        result = self.parse_json_response(raw)
        logger.info(
            f"[AGENT: {self.name}] ✓ Complete | "
            f"Veto: {result.get('veto_flag')} | "
            f"Confidence: {result.get('confidence_score')}"
        )
        return result