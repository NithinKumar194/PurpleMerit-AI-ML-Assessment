"""
tools/feedback_tools.py
Programmatic tools called by Marketing/Comms Agent.
Tool 4: summarize_sentiment  — classify + count sentiment
Tool 5: extract_themes       — find repeated issue keywords
"""

import logging
from collections import Counter

logger = logging.getLogger("war_room.tools.feedback")

# Keyword lists for rule-based theme extraction
THEME_KEYWORDS = {
    "payment_failure":   ["payment", "charged", "charge", "failed", "failure", "checkout", "pay"],
    "double_charge":     ["twice", "double", "charged twice", "two charges", "duplicate"],
    "app_crash":         ["crash", "crashes", "crashing", "broken", "unusable", "cannot open"],
    "slow_performance":  ["slow", "loading", "latency", "takes", "seconds", "wait"],
    "data_loss":         ["lost", "settings", "saved", "preferences", "missing"],
    "support_failure":   ["support", "ticket", "response", "reply", "no reply", "no response"],
    "churn_signal":      ["cancel", "cancelling", "switching", "competitor", "subscription", "leaving"],
    "positive_ux":       ["love", "clean", "intuitive", "smooth", "better", "faster", "good"]
}


def summarize_sentiment(feedback_entries: list) -> dict:
    """
    Tool 4: Classify feedback entries into positive/neutral/negative.
    Uses hint field + simple keyword scoring.
    Called by: Marketing/Comms Agent
    """
    logger.info("[TOOL CALL] summarize_sentiment() invoked")

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    by_day = {}
    negative_entries = []

    for entry in feedback_entries:
        sentiment = entry.get("sentiment_hint", "neutral")
        counts[sentiment] = counts.get(sentiment, 0) + 1

        day = entry.get("day", 0)
        if day not in by_day:
            by_day[day] = {"positive": 0, "neutral": 0, "negative": 0}
        by_day[day][sentiment] = by_day[day].get(sentiment, 0) + 1

        if sentiment == "negative":
            negative_entries.append(entry.get("text", ""))

    total = sum(counts.values())
    result = {
        "total_entries": total,
        "counts": counts,
        "percentages": {
            k: round((v / total) * 100, 1) for k, v in counts.items()
        },
        "sentiment_by_day": by_day,
        "overall_sentiment": (
            "NEGATIVE" if counts["negative"] > counts["positive"]
            else "POSITIVE" if counts["positive"] > counts["negative"]
            else "NEUTRAL"
        ),
        "top_negative_samples": negative_entries[:5]
    }

    logger.info(
        f"[TOOL RESULT] summarize_sentiment() → "
        f"Positive:{counts['positive']} Neutral:{counts['neutral']} "
        f"Negative:{counts['negative']} | Overall: {result['overall_sentiment']}"
    )
    return result


def extract_themes(feedback_entries: list) -> dict:
    """
    Tool 5: Extract repeated issue themes from feedback text.
    Returns theme counts and most critical themes.
    Called by: Marketing/Comms Agent, Risk Agent
    """
    logger.info("[TOOL CALL] extract_themes() invoked")

    theme_counts = {theme: 0 for theme in THEME_KEYWORDS}
    theme_examples = {theme: [] for theme in THEME_KEYWORDS}

    for entry in feedback_entries:
        text = entry.get("text", "").lower()
        for theme, keywords in THEME_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    theme_counts[theme] += 1
                    if len(theme_examples[theme]) < 2:
                        theme_examples[theme].append(entry.get("text", ""))
                    break

    # Sort themes by frequency
    sorted_themes = sorted(
        [(t, c) for t, c in theme_counts.items() if c > 0],
        key=lambda x: x[1],
        reverse=True
    )

    # Flag legally/financially dangerous themes
    high_risk_themes = []
    if theme_counts.get("double_charge", 0) >= 2:
        high_risk_themes.append({
            "theme": "double_charge",
            "count": theme_counts["double_charge"],
            "risk_level": "CRITICAL",
            "reason": "Financial harm to users — chargeback and legal exposure risk"
        })
    if theme_counts.get("churn_signal", 0) >= 2:
        high_risk_themes.append({
            "theme": "churn_signal",
            "count": theme_counts["churn_signal"],
            "risk_level": "HIGH",
            "reason": "Active churn mentions — revenue loss in progress"
        })

    result = {
        "theme_counts": theme_counts,
        "ranked_themes": [{"theme": t, "count": c} for t, c in sorted_themes],
        "high_risk_themes": high_risk_themes,
        "top_theme": sorted_themes[0][0] if sorted_themes else "none",
        "theme_examples": {
            t: ex for t, ex in theme_examples.items() if ex
        }
    }

    logger.info(
        f"[TOOL RESULT] extract_themes() → "
        f"Top theme: {result['top_theme']} | "
        f"High-risk themes: {len(high_risk_themes)}"
    )
    return result