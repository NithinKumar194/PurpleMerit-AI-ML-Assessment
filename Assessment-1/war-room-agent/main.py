"""
main.py
War Room Multi-Agent System — Entry Point
Uses OpenAI GPT-4o via OPENAI_API_KEY environment variable.

Usage:
    python main.py

Output:
    - Console summary of final decision
    - output/final_decision.json  (canonical output)
    - output/final_decision_TIMESTAMP.json (per-run copy)
    - logs/run_trace_TIMESTAMP.log (full agent trace)
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# ── Load .env file first ──────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Create required directories ───────────────────────────────
Path("logs").mkdir(exist_ok=True)
Path("output").mkdir(exist_ok=True)

# ── Logging Setup ─────────────────────────────────────────────
timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
log_file  = f"logs/run_trace_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-35s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("war_room.main")

# ── Validate Environment Variable ─────────────────────────────
if not os.environ.get("OPENAI_API_KEY"):
    logger.error("❌ OPENAI_API_KEY is not set.")
    logger.error("   Create a .env file with: OPENAI_API_KEY=sk-your-key-here")
    logger.error("   Or export it: export OPENAI_API_KEY=sk-your-key-here")
    sys.exit(1)

logger.info("✅ OPENAI_API_KEY loaded from environment")

# ── Import orchestrator after env check ───────────────────────
from orchestrator import WarRoomOrchestrator


# ──────────────────────────────────────────────────────────────
def load_data() -> dict:
    """Load all three input files from data/ directory."""
    logger.info("[MAIN] Loading input data files...")

    # Metrics
    metrics_path = Path("data/metrics.json")
    if not metrics_path.exists():
        logger.error(f"❌ Missing: {metrics_path}")
        sys.exit(1)
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    logger.info(
        f"[MAIN] ✅ Loaded metrics.json | "
        f"Feature: {metrics.get('feature')} | "
        f"Days: {len(metrics['time_series']['days'])}"
    )

    # Feedback
    feedback_path = Path("data/feedback.json")
    if not feedback_path.exists():
        logger.error(f"❌ Missing: {feedback_path}")
        sys.exit(1)
    with open(feedback_path, "r", encoding="utf-8") as f:
        feedback = json.load(f)
    logger.info(
        f"[MAIN] ✅ Loaded feedback.json | "
        f"Entries: {feedback.get('total_entries')}"
    )

    # Release notes
    notes_path = Path("data/release_notes.md")
    if not notes_path.exists():
        logger.error(f"❌ Missing: {notes_path}")
        sys.exit(1)
    with open(notes_path, "r", encoding="utf-8") as f:
        release_notes = f.read()
    logger.info(
        f"[MAIN] ✅ Loaded release_notes.md | "
        f"Size: {len(release_notes)} chars"
    )

    return {
        "metrics":       metrics,
        "feedback":      feedback,
        "release_notes": release_notes
    }


def save_output(result: dict) -> str:
    """Save final JSON to output/ directory."""
    # Timestamped copy
    ts_path = f"output/final_decision_{timestamp}.json"
    with open(ts_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Canonical always-overwritten file
    canonical = "output/final_decision.json"
    with open(canonical, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"[MAIN] ✅ Output saved → {ts_path}")
    logger.info(f"[MAIN] ✅ Canonical   → {canonical}")
    return canonical


def print_console_summary(result: dict):
    """Print a clean human-readable summary to console."""
    decision = result.get("decision", "UNKNOWN")
    cs       = result.get("confidence_score", {})
    score    = cs.get("score", "?")
    rating   = cs.get("rating", "?")
    rationale = result.get("rationale", {})
    risks    = result.get("risk_register", [])
    actions  = result.get("action_plan", [])
    meta     = result.get("metadata", {})

    # Decision banner with visual emphasis
    banner = {
        "ROLL_BACK": "🔴  DECISION: ROLL BACK",
        "PAUSE":     "🟡  DECISION: PAUSE",
        "PROCEED":   "🟢  DECISION: PROCEED"
    }.get(decision, f"⚪  DECISION: {decision}")

    print("\n" + "=" * 65)
    print(f"  WAR ROOM — FINAL DECISION REPORT")
    print(f"  Feature: {meta.get('feature', 'Unknown')}")
    print(f"  Timestamp: {meta.get('session_timestamp', 'Unknown')}")
    print("=" * 65)
    print(f"\n  {banner}")
    print(f"  CONFIDENCE: {score}% ({rating})\n")
    print("-" * 65)
    print(f"  SUMMARY:\n  {rationale.get('summary', '')}")
    print("\n  KEY DRIVERS:")
    for d in rationale.get("key_drivers", []):
        print(f"    • {d}")
    print("\n  TOP RISKS:")
    for r in risks[:4]:
        print(f"    [{r.get('severity', '?')}] {r.get('risk', '')}")
        print(f"           → {r.get('mitigation', '')}")
    print("\n  IMMEDIATE ACTIONS (24–48 hours):")
    for a in actions[:5]:
        print(
            f"    {a.get('priority')}. [{a.get('deadline')}] "
            f"{a.get('action')}"
        )
        print(f"       Owner: {a.get('owner')} | Done when: {a.get('success_criteria')}")
    print("\n  WHAT WOULD INCREASE CONFIDENCE:")
    for gap in cs.get("what_would_increase_confidence", [])[:3]:
        print(f"    • {gap}")
    print("-" * 65)
    print(f"  📄 Full JSON  → output/final_decision.json")
    print(f"  📋 Trace Log  → {log_file}")
    print("=" * 65 + "\n")


# ──────────────────────────────────────────────────────────────
def main():
    logger.info("=" * 65)
    logger.info("  WAR ROOM MULTI-AGENT SYSTEM — STARTING")
    logger.info(f"  Log File: {log_file}")
    logger.info("=" * 65)

    # 1. Load all input data
    data = load_data()

    # 2. Run the orchestrator (all agents execute here)
    orchestrator = WarRoomOrchestrator(data)
    result = orchestrator.run()

    # 3. Save output JSON
    save_output(result)

    # 4. Print human-readable summary
    print_console_summary(result)

    logger.info("[MAIN] ✅ System complete. Exiting.")
    return result


if __name__ == "__main__":
    main()