import json
import logging
from agents.base_agent import BaseAgent
from tools.metric_tools import detect_anomalies

logger = logging.getLogger("war_room.agents.sre")

SRE_SYSTEM = """You are the Site Reliability Engineer (SRE) in a product launch war room.
Your job is purely technical reliability assessment.
You must:
- Determine precisely which SLAs are breached and since when
- Assess trajectory: is the system stabilizing or degrading further?
- Estimate blast radius: how many users are being impacted right now?
- Give a clear reliability verdict independent of business considerations

Respond ONLY in valid JSON with exactly these keys:
{
  "sla_breach_assessment": "string summary",
  "sla_breaches": [
    {"metric": "string", "threshold": "value", "current": "value", "breached_since": "DayX", "severity": "CRITICAL|HIGH"}
  ],
  "infrastructure_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "blast_radius_estimate": "string estimate of users affected",
  "reliability_verdict": "string",
  "preliminary_recommendation": "PROCEED|PAUSE|ROLL_BACK"
}"""


class SREAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SRE/Reliability Agent",
            role_description="Assesses SLA compliance, infrastructure risk, and reliability verdict"
        )

    def analyze(self, time_series: dict, thresholds: dict, analyst_output: dict) -> dict:
        logger.info(f"[AGENT: {self.name}] ── Starting Analysis ──")

        logger.info(f"[AGENT: {self.name}] → Invoking Tool: detect_anomalies()")
        anomalies = detect_anomalies(time_series, thresholds)

        user_msg = f"""
SLA THRESHOLDS DEFINED:
{json.dumps(thresholds, indent=2)}

ANOMALY / BREACH REPORT (from tool):
{json.dumps(anomalies, indent=2)}

DATA ANALYST CONTEXT:
{json.dumps(analyst_output.get('critical_findings', []), indent=2)}

Provide your SRE reliability assessment in JSON.
"""
        raw = self.call_llm(SRE_SYSTEM, user_msg)
        result = self.parse_json_response(raw)
        result["_tool_outputs"] = {"anomalies": anomalies}
        logger.info(
            f"[AGENT: {self.name}] ✓ Complete | "
            f"Verdict: {result.get('reliability_verdict', '')[:60]} | "
            f"Infra Risk: {result.get('infrastructure_risk_level')}"
        )
        return result