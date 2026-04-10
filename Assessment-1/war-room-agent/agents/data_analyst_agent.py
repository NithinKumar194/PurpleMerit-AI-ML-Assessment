import json
import logging
from agents.base_agent import BaseAgent
from tools.metric_tools import aggregate_metrics, detect_anomalies, compare_to_baseline

logger = logging.getLogger("war_room.agents.data_analyst")

DA_SYSTEM = """You are the Data Analyst in a product launch war room.
Your job is to interpret quantitative metric data objectively and rigorously.
You receive pre-computed metric aggregations, anomaly reports, and baseline comparisons.
You must:
- Identify the most critical metric trends with specific numbers
- Assess whether metrics are stabilizing or accelerating in the wrong direction
- State your confidence level in the data (0-100)
- Give a preliminary quantitative recommendation: PROCEED, PAUSE, or ROLL_BACK

Respond ONLY in valid JSON with exactly these keys:
{
  "critical_findings": ["finding1", "finding2", ...],
  "trend_assessment": "string describing overall trend direction",
  "anomaly_summary": "string summarizing key threshold breaches",
  "confidence_level": 0-100,
  "preliminary_recommendation": "PROCEED|PAUSE|ROLL_BACK",
  "key_metric_references": ["metric: value context", ...]
}"""


class DataAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Data Analyst Agent",
            role_description="Analyses quantitative metrics, trends, anomalies, and confidence"
        )

    def analyze(self, time_series: dict, thresholds: dict, baseline: dict) -> dict:
        logger.info(f"[AGENT: {self.name}] ── Starting Analysis ──")

        # TOOL CALLS — programmatic, not LLM
        logger.info(f"[AGENT: {self.name}] → Invoking Tool: aggregate_metrics()")
        agg = aggregate_metrics(time_series)

        logger.info(f"[AGENT: {self.name}] → Invoking Tool: detect_anomalies()")
        anomalies = detect_anomalies(time_series, thresholds)

        logger.info(f"[AGENT: {self.name}] → Invoking Tool: compare_to_baseline()")
        baseline_delta = compare_to_baseline(time_series, baseline)

        user_msg = f"""
Here are the pre-computed tool outputs for your analysis:

AGGREGATED METRICS:
{json.dumps(agg, indent=2)}

ANOMALY / THRESHOLD BREACH REPORT:
{json.dumps(anomalies, indent=2)}

BASELINE COMPARISON (current vs pre-launch):
{json.dumps(baseline_delta, indent=2)}

Based on these tool outputs, provide your Data Analyst assessment in JSON format.
"""
        raw = self.call_llm(DA_SYSTEM, user_msg)
        result = self.parse_json_response(raw)

        # Attach tool outputs for downstream agents
        result["_tool_outputs"] = {
            "aggregated_metrics": agg,
            "anomalies": anomalies,
            "baseline_comparison": baseline_delta
        }
        logger.info(
            f"[AGENT: {self.name}] ✓ Complete | "
            f"Recommendation: {result.get('preliminary_recommendation')} | "
            f"Confidence: {result.get('confidence_level')}"
        )
        return result