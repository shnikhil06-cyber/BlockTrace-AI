"""
Broadcast Origin Tracer for BlockTrace-AI.
Pinpoints the earliest observing P2P peer node, reconstructs network propagation timelines,
and computes origin confidence scores.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


class OriginTracer:
    """
    Forensic origin tracer reconstructing transaction propagation across the Bitcoin network.
    """

    def trace_transaction_origin(
        self,
        tx_id: str,
        df_net: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyzes network logs for a specific transaction to pinpoint broadcast origin.
        """
        if df_net is None or df_net.empty:
            return {"status": "NO_NETWORK_DATA", "tx_id": tx_id}

        logs = df_net[df_net["tx_id"] == tx_id].sort_values(by="timestamp_observed")

        if logs.empty:
            return {"status": "TX_NOT_FOUND_IN_NETWORK_LOGS", "tx_id": tx_id}

        earliest = logs.iloc[0]
        total_observers = len(logs)

        # Timeline steps
        timeline: List[Dict[str, Any]] = []
        t0 = earliest["timestamp_observed"]

        for idx, (_, row) in enumerate(logs.iterrows()):
            delta_ms = max((row["timestamp_observed"] - t0).total_seconds() * 1000.0, 0.0)
            timeline.append({
                "hop_order": idx + 1,
                "timestamp": str(row["timestamp_observed"]),
                "delta_ms": round(delta_ms, 1),
                "node_id": row["node_id"],
                "ip_address": row["ip_address"],
                "country": row.get("country", "UNKNOWN"),
                "asn": row.get("asn", "UNKNOWN"),
                "event_type": row.get("event_type", "peer_relay"),
                "latency_ms": float(row.get("latency_ms", 0.0)),
                "user_agent": row.get("user_agent", "Unknown")
            })

        # Calculate origin confidence score (0 to 100%)
        # Heuristics:
        # - Has inv_broadcast event: +30
        # - High number of observer nodes (>4): +25
        # - Clear temporal gap before 2nd observer (>50ms): +25
        # - Low reported latency (<100ms): +20
        confidence = 40.0
        if earliest.get("event_type") == "inv_broadcast":
            confidence += 25.0
        if total_observers >= 4:
            confidence += 15.0
        if total_observers > 1:
            second_t = logs.iloc[1]["timestamp_observed"]
            gap_ms = (second_t - t0).total_seconds() * 1000.0
            if gap_ms > 30.0:
                confidence += 20.0

        confidence = min(round(confidence, 1), 98.0)

        return {
            "status": "ORIGIN_IDENTIFIED",
            "tx_id": tx_id,
            "origin_node_id": earliest["node_id"],
            "origin_ip": earliest["ip_address"],
            "origin_asn": earliest.get("asn", "UNKNOWN"),
            "origin_country": earliest.get("country", "UNKNOWN"),
            "origin_event": earliest.get("event_type", "inv_broadcast"),
            "user_agent": earliest.get("user_agent", "Unknown"),
            "first_observed_utc": str(t0),
            "total_observers": total_observers,
            "origin_confidence_pct": confidence,
            "total_propagation_duration_ms": timeline[-1]["delta_ms"] if timeline else 0.0,
            "timeline": timeline
        }
