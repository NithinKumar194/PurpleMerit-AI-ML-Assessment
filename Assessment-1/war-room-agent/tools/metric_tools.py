"""
tools/metric_tools.py
Programmatic tools called by Data Analyst Agent and SRE Agent.
Tool 1: aggregate_metrics  — computes stats + trends
Tool 2: detect_anomalies   — flags threshold breaches
Tool 3: compare_to_baseline — computes delta vs pre-launch
"""

import json
import logging

logger = logging.getLogger("war_room.tools.metric")


def aggregate_metrics(time_series: dict) -> dict:
    """
    Tool 1: Aggregate raw time-series metrics.
    Returns mean, min, max, latest value, and trend direction
    for every metric in the time series.
    Called by: Data Analyst Agent
    """
    logger.info("[TOOL CALL] aggregate_metrics() invoked")
    days = time_series.get("days", [])
    results = {}

    skip_keys = {"days"}
    for metric, values in time_series.items():
        if metric in skip_keys:
            continue
        if not values:
            continue

        avg = round(sum(values) / len(values), 4)
        minimum = round(min(values), 4)
        maximum = round(max(values), 4)
        latest = round(values[-1], 4)
        first = round(values[0], 4)

        # Trend: compare last 3 days avg vs first 3 days avg
        if len(values) >= 6:
            early_avg = sum(values[:3]) / 3
            late_avg = sum(values[-3:]) / 3
            pct_change = round(((late_avg - early_avg) / early_avg) * 100, 2)
            if pct_change > 5:
                trend = "WORSENING" if metric in [
                    "crash_rate_pct", "api_latency_p95_ms",
                    "support_ticket_volume", "churn_rate_daily"
                ] else "IMPROVING"
            elif pct_change < -5:
                trend = "IMPROVING" if metric in [
                    "crash_rate_pct", "api_latency_p95_ms",
                    "support_ticket_volume", "churn_rate_daily"
                ] else "WORSENING"
            else:
                trend = "STABLE"
        else:
            pct_change = 0
            trend = "INSUFFICIENT_DATA"

        results[metric] = {
            "mean": avg,
            "min": minimum,
            "max": maximum,
            "latest_value": latest,
            "first_value": first,
            "pct_change_overall": round(((latest - first) / first) * 100, 2),
            "trend": trend,
            "days_tracked": len(values)
        }

    logger.info(f"[TOOL RESULT] aggregate_metrics() → {len(results)} metrics processed")
    return results


def detect_anomalies(time_series: dict, thresholds: dict) -> dict:
    """
    Tool 2: Detect threshold breaches in metrics.
    Returns list of CRITICAL and WARNING breaches with day info.
    Called by: Data Analyst Agent, SRE Agent
    """
    logger.info("[TOOL CALL] detect_anomalies() invoked")
    anomalies = {"critical": [], "warning": [], "summary": {}}
    days = time_series.get("days", [])

    for metric, values in time_series.items():
        if metric == "days" or metric not in thresholds:
            continue

        t = thresholds[metric]
        warn_val = t.get("warning")
        crit_val = t.get("critical")

        # Metrics where HIGHER = WORSE
        higher_is_worse = {
            "crash_rate_pct", "api_latency_p95_ms",
            "support_ticket_volume", "churn_rate_daily"
        }

        crit_breach_days = []
        warn_breach_days = []

        for i, val in enumerate(values):
            day = days[i] if i < len(days) else f"Day{i+1}"

            if metric in higher_is_worse:
                if crit_val is not None and val >= crit_val:
                    crit_breach_days.append({"day": day, "value": val, "threshold": crit_val})
                elif warn_val is not None and val >= warn_val:
                    warn_breach_days.append({"day": day, "value": val, "threshold": warn_val})
            else:
                # Lower is worse (payment_success, funnel_completion etc.)
                if crit_val is not None and val <= crit_val:
                    crit_breach_days.append({"day": day, "value": val, "threshold": crit_val})
                elif warn_val is not None and val <= warn_val:
                    warn_breach_days.append({"day": day, "value": val, "threshold": warn_val})

        if crit_breach_days:
            anomalies["critical"].append({
                "metric": metric,
                "breach_count": len(crit_breach_days),
                "first_breach": crit_breach_days[0],
                "latest_breach": crit_breach_days[-1],
                "severity": "CRITICAL"
            })
        elif warn_breach_days:
            anomalies["warning"].append({
                "metric": metric,
                "breach_count": len(warn_breach_days),
                "first_breach": warn_breach_days[0],
                "latest_breach": warn_breach_days[-1],
                "severity": "WARNING"
            })

    anomalies["summary"] = {
        "total_critical_breaches": len(anomalies["critical"]),
        "total_warning_breaches": len(anomalies["warning"]),
        "critical_metrics": [a["metric"] for a in anomalies["critical"]],
        "warning_metrics": [a["metric"] for a in anomalies["warning"]]
    }

    logger.info(
        f"[TOOL RESULT] detect_anomalies() → "
        f"{len(anomalies['critical'])} CRITICAL, "
        f"{len(anomalies['warning'])} WARNING"
    )
    return anomalies


def compare_to_baseline(time_series: dict, baseline: dict) -> dict:
    """
    Tool 3: Compare current (latest day) values against pre-launch baseline.
    Returns percentage delta for each metric.
    Called by: PM Agent
    """
    logger.info("[TOOL CALL] compare_to_baseline() invoked")
    comparison = {}

    for metric, values in time_series.items():
        if metric == "days":
            continue
        if metric not in baseline:
            continue

        latest = values[-1]
        base = baseline[metric]
        delta_pct = round(((latest - base) / base) * 100, 2)

        # Determine if this delta is good or bad
        higher_is_worse = {
            "crash_rate_pct", "api_latency_p95_ms",
            "support_ticket_volume", "churn_rate_daily"
        }

        if metric in higher_is_worse:
            status = "DEGRADED" if delta_pct > 10 else ("STABLE" if delta_pct > -10 else "IMPROVED")
        else:
            status = "DEGRADED" if delta_pct < -5 else ("STABLE" if delta_pct < 5 else "IMPROVED")

        comparison[metric] = {
            "baseline": base,
            "current": latest,
            "delta_pct": delta_pct,
            "status": status
        }

    logger.info(f"[TOOL RESULT] compare_to_baseline() → {len(comparison)} metrics compared")
    return comparison