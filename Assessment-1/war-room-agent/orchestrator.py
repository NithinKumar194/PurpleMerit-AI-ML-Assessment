"""
orchestrator.py
Master coordinator — War Room Multi-Agent System.
Uses OpenAI GPT-4o. API key loaded from OPENAI_API_KEY env variable.

Agent Execution Flow (Sequential with context passing):
  Step 1 → Data Analyst Agent   (Tools: aggregate_metrics, detect_anomalies, compare_to_baseline)
  Step 2 → Product Manager Agent (Reads: Step 1 output + release notes)
  Step 3 → Marketing/Comms Agent (Tools: summarize_sentiment, extract_themes)
  Step 4 → SRE/Reliability Agent (Tool: detect_anomalies | Bonus Agent)
  Step 5 → Risk/Critic Agent     (Reads: All Steps 1-4 outputs)
  Step 6 → Orchestrator Synthesis → Final JSON Decision
"""

import json
import logging
import os
from datetime import datetime, timezone
from openai import OpenAI

from agents.data_analyst_agent import DataAnalystAgent
from agents.pm_agent import PMAgent
from agents.marketing_agent import MarketingAgent
from agents.risk_agent import RiskAgent
from agents.sre_agent import SREAgent

logger = logging.getLogger("war_room.orchestrator")

ORCHESTRATOR_SYSTEM = """You are the War Room Orchestrator — the final decision authority.
You have received full assessments from 5 specialist agents. Synthesize them into one final decision.

Decision options: PROCEED / PAUSE / ROLL_BACK

Synthesis rules:
1. If Risk/Critic Agent issued veto_flag=true → decision must be ROLL_BACK or PAUSE (justify if overriding)
2. If 3 or more agents recommend ROLL_BACK → decision must be ROLL_BACK
3. Use Risk Agent's confidence_score as the basis for final confidence_score
4. Every action_plan item must have a specific owner, deadline, and success_criteria
5. communication_plan must cover both internal AND external audiences with specific messages

You MUST respond in valid JSON matching EXACTLY this structure — no extra keys, no missing keys:
{
  "decision": "PROCEED|PAUSE|ROLL_BACK",
  "rationale": {
    "summary": "2-3 sentence executive summary",
    "key_drivers": ["driver1", "driver2", "driver3", "driver4"],
    "metric_references": ["metric: value — context", "metric: value — context"],
    "feedback_summary": "string summarizing user feedback themes and sentiment numbers"
  },
  "risk_register": [
    {
      "risk": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "mitigation": "specific action string",
      "owner": "role/team string"
    }
  ],
  "action_plan": [
    {
      "priority": 1,
      "action": "specific action string",
      "owner": "role/team string",
      "deadline": "Within X hours/days",
      "success_criteria": "how we know this is done"
    }
  ],
  "communication_plan": {
    "internal": {
      "audience": "string",
      "message": "string",
      "channel": "string",
      "timing": "string"
    },
    "external": {
      "audience": "string",
      "message": "string",
      "channel": "string",
      "timing": "string"
    }
  },
  "confidence_score": {
    "score": 0,
    "rating": "LOW|MEDIUM|HIGH",
    "what_would_increase_confidence": ["item1", "item2", "item3"]
  },
  "agent_votes": {},
  "metadata": {}
}"""


class WarRoomOrchestrator:

    def __init__(self, data: dict):
        self.data = data
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = "gpt-4o"
        self.agent_outputs = {}

        # Initialise all agents
        self.da_agent  = DataAnalystAgent()
        self.pm_agent  = PMAgent()
        self.mkt_agent = MarketingAgent()
        self.sre_agent = SREAgent()
        self.risk_agent = RiskAgent()

    def run(self) -> dict:
        logger.info("=" * 65)
        logger.info("  WAR ROOM SESSION STARTED")
        logger.info(f"  Feature      : {self.data['metrics'].get('feature')}")
        logger.info(f"  Launch Date  : {self.data['metrics'].get('launch_date')}")
        logger.info(f"  Report Date  : {self.data['metrics'].get('report_date')}")
        logger.info(f"  Days Tracked : {len(self.data['metrics']['time_series']['days'])}")
        logger.info("=" * 65)

        ts          = self.data["metrics"]["time_series"]
        thresholds  = self.data["metrics"]["thresholds"]
        baseline    = self.data["metrics"]["baseline_pre_launch"]
        feedback    = self.data["feedback"]["entries"]
        rel_notes   = self.data["release_notes"]

        # ── Step 1: Data Analyst ──────────────────────────────────
        logger.info("\n[ORCHESTRATOR] ➤ Step 1: Dispatching Data Analyst Agent")
        da_out = self.da_agent.analyze(ts, thresholds, baseline)
        self.agent_outputs["data_analyst"] = da_out
        logger.info("[ORCHESTRATOR] ✓ Step 1 Complete\n")

        # ── Step 2: Product Manager ───────────────────────────────
        logger.info("[ORCHESTRATOR] ➤ Step 2: Dispatching Product Manager Agent")
        pm_out = self.pm_agent.analyze(rel_notes, da_out)
        self.agent_outputs["product_manager"] = pm_out
        logger.info("[ORCHESTRATOR] ✓ Step 2 Complete\n")

        # ── Step 3: Marketing / Comms ─────────────────────────────
        logger.info("[ORCHESTRATOR] ➤ Step 3: Dispatching Marketing/Comms Agent")
        mkt_out = self.mkt_agent.analyze(feedback)
        self.agent_outputs["marketing_comms"] = mkt_out
        logger.info("[ORCHESTRATOR] ✓ Step 3 Complete\n")

        # ── Step 4: SRE (Bonus Agent) ─────────────────────────────
        logger.info("[ORCHESTRATOR] ➤ Step 4: Dispatching SRE/Reliability Agent [BONUS]")
        sre_out = self.sre_agent.analyze(ts, thresholds, da_out)
        self.agent_outputs["sre_reliability"] = sre_out
        logger.info("[ORCHESTRATOR] ✓ Step 4 Complete\n")

        # ── Step 5: Risk / Critic ─────────────────────────────────
        logger.info("[ORCHESTRATOR] ➤ Step 5: Dispatching Risk/Critic Agent")
        risk_out = self.risk_agent.analyze(da_out, pm_out, mkt_out)
        self.agent_outputs["risk_critic"] = risk_out
        logger.info("[ORCHESTRATOR] ✓ Step 5 Complete\n")

        # ── Collect Votes ─────────────────────────────────────────
        votes = {
            "data_analyst":    da_out.get("preliminary_recommendation", "UNKNOWN"),
            "product_manager": pm_out.get("preliminary_recommendation", "UNKNOWN"),
            "marketing_comms": mkt_out.get("preliminary_recommendation", "UNKNOWN"),
            "sre_reliability": sre_out.get("preliminary_recommendation", "UNKNOWN"),
            "risk_critic_veto": risk_out.get("veto_flag", False)
        }
        logger.info(f"[ORCHESTRATOR] Agent Votes Collected:\n{json.dumps(votes, indent=4)}")

        # ── Step 6: Final Synthesis ───────────────────────────────
        logger.info("\n[ORCHESTRATOR] ➤ Step 6: Synthesizing Final Decision...")
        final = self._synthesize_final_decision(votes)

        # Inject metadata
        final["agent_votes"] = votes
        final["metadata"] = {
            "session_timestamp":  datetime.now(timezone.utc).isoformat(),
            "feature":            self.data["metrics"].get("feature"),
            "launch_date":        self.data["metrics"].get("launch_date"),
            "report_date":        self.data["metrics"].get("report_date"),
            "days_since_launch":  len(ts["days"]),
            "model_used":         self.model,
            "agents_consulted":   list(self.agent_outputs.keys()),
            "tools_invoked": [
                "aggregate_metrics",
                "detect_anomalies",
                "compare_to_baseline",
                "summarize_sentiment",
                "extract_themes"
            ]
        }

        logger.info(f"\n{'='*65}")
        logger.info(f"  FINAL DECISION  : {final.get('decision')}")
        logger.info(f"  CONFIDENCE      : {final.get('confidence_score', {}).get('score')}% "
                    f"({final.get('confidence_score', {}).get('rating')})")
        logger.info(f"{'='*65}")
        logger.info("  WAR ROOM SESSION COMPLETE")
        logger.info(f"{'='*65}\n")

        return final

    def _synthesize_final_decision(self, votes: dict) -> dict:
        """Orchestrator's own LLM call to synthesize all agent outputs into final JSON."""

        # Build clean agent summaries (strip internal _tool_outputs keys)
        def clean(d):
            return {k: v for k, v in d.items() if not k.startswith('_')}

        all_outputs_clean = {
            agent: clean(output)
            for agent, output in self.agent_outputs.items()
        }

        user_msg = f"""
You have all 5 agent assessments below. Synthesize them into the final war room decision.

ALL AGENT OUTPUTS:
{json.dumps(all_outputs_clean, indent=2)}

AGENT PRELIMINARY VOTES:
{json.dumps(votes, indent=2)}

Risk Critic Confidence Score: {self.agent_outputs['risk_critic'].get('confidence_score', 75)}

Produce the complete final decision JSON now.
"""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM},
                {"role": "user",   "content": user_msg}
            ]
        )

        raw = response.choices[0].message.content
        logger.info(
            f"[ORCHESTRATOR] Synthesis LLM call complete "
            f"(tokens={response.usage.total_tokens})"
        )

        # Strip fences just in case
        cleaned = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(cleaned)