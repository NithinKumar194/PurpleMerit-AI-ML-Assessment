import json
import logging
from agents.base_agent import BaseAgent
from tools.feedback_tools import summarize_sentiment, extract_themes

logger = logging.getLogger("war_room.agents.marketing")

MKT_SYSTEM = """You are the Marketing and Communications lead in a product launch war room.
Your job is to assess customer perception, brand risk, and communication strategy.
You must:
- Interpret sentiment and feedback themes with specific numbers
- Identify reputational risks: what is the public narrative forming?
- Flag any legally or financially dangerous feedback patterns (e.g. double charges, fraud claims)
- Recommend precise internal and external communication actions

Respond ONLY in valid JSON with exactly these keys:
{
  "sentiment_assessment": "string with numbers (X% negative, Y% positive)",
  "top_issues": ["issue1 (count)", "issue2 (count)", ...],
  "reputational_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "legal_risk_flags": ["flag1", "flag2"],
  "communication_recommendations": {
    "internal": "string",
    "external": "string"
  },
  "preliminary_recommendation": "PROCEED|PAUSE|ROLL_BACK"
}"""


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Marketing/Comms Agent",
            role_description="Assesses messaging, customer perception, and communication actions"
        )

    def analyze(self, feedback_entries: list) -> dict:
        logger.info(f"[AGENT: {self.name}] ── Starting Analysis ──")

        # TOOL CALLS
        logger.info(f"[AGENT: {self.name}] → Invoking Tool: summarize_sentiment()")
        sentiment = summarize_sentiment(feedback_entries)

        logger.info(f"[AGENT: {self.name}] → Invoking Tool: extract_themes()")
        themes = extract_themes(feedback_entries)

        user_msg = f"""
SENTIMENT ANALYSIS RESULTS (from tool):
{json.dumps(sentiment, indent=2)}

THEME EXTRACTION RESULTS (from tool):
{json.dumps(themes, indent=2)}

Based on the above tool outputs, provide your Marketing and Communications assessment in JSON.
"""
        raw = self.call_llm(MKT_SYSTEM, user_msg)
        result = self.parse_json_response(raw)
        result["_tool_outputs"] = {"sentiment": sentiment, "themes": themes}
        logger.info(
            f"[AGENT: {self.name}] ✓ Complete | "
            f"Recommendation: {result.get('preliminary_recommendation')} | "
            f"Reputational Risk: {result.get('reputational_risk_level')}"
        )
        return result