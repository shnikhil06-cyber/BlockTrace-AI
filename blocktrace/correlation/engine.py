"""
Correlation Engine for BlockTrace-AI.
Links on-chain Bitcoin transaction records with off-chain P2P network observation logs.
Computes propagation timing, identifies broadcast origins, detects anonymizer relays,
and aggregates network-level forensic indicators.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from blocktrace.ingestion.parsers import normalize_tx_id


@dataclass
class CorrelationSummary:
    total_txs: int
    matched_txs: int
    unmatched_txs: int
    correlation_rate_pct: float
    total_network_logs: int
    unique_origin_ips: int
    unique_countries: int
    tor_proxy_broadcasts: int
    bulletproof_broadcasts: int
    avg_propagation_spread_ms: float
    avg_confirmation_delay_sec: float


class CorrelationEngine:
    """
    Correlates blockchain transaction records with peer-to-peer network telemetry.
    """

    KNOWN_TOR_ASNS = {"AS200052", "AS60729", "AS9009", "AS197071"}
    KNOWN_BULLETPROOF_ASNS = {"AS49981", "AS202425", "AS58224", "AS210644"}

    def __init__(self, time_tolerance_sec: int = 7200):
        self.time_tolerance_sec = time_tolerance_sec

    def correlate(
        self,
        df_tx: pd.DataFrame,
        df_net: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Executes cross-source correlation between transaction records and network logs.
        Returns an enriched transaction dataframe with network metrics.
        """
        df_tx_clean = df_tx.copy()

        if df_net is None or df_net.empty:
            # Assign neutral defaults when network logs are absent
            df_tx_clean["network_correlated"] = False
            df_tx_clean["observed_node_count"] = 0
            df_tx_clean["first_seen_timestamp"] = df_tx_clean["timestamp"]
            df_tx_clean["confirmation_delay_sec"] = 0.0
            df_tx_clean["propagation_spread_ms"] = 0.0
            df_tx_clean["mean_latency_ms"] = 0.0
            df_tx_clean["earliest_ip"] = "N/A"
            df_tx_clean["earliest_node_id"] = "N/A"
            df_tx_clean["earliest_asn"] = "N/A"
            df_tx_clean["earliest_country"] = "UNKNOWN"
            df_tx_clean["earliest_event"] = "N/A"
            df_tx_clean["relay_ips"] = [[] for _ in range(len(df_tx_clean))]
            df_tx_clean["relay_asns"] = [[] for _ in range(len(df_tx_clean))]
            df_tx_clean["relay_countries"] = [[] for _ in range(len(df_tx_clean))]
            df_tx_clean["is_tor_proxy_origin"] = False
            df_tx_clean["is_bulletproof_origin"] = False
            df_tx_clean["burst_velocity"] = 0.0
            df_tx_clean["correlation_status"] = "NO_NETWORK_DATA"
            return df_tx_clean

        df_net_clean = df_net.copy()
        df_tx_clean["tx_id"] = df_tx_clean["tx_id"].apply(normalize_tx_id)
        df_net_clean["tx_id"] = df_net_clean["tx_id"].apply(normalize_tx_id)

        # Smart prefix / truncated hash alignment if exact matching is incomplete
        tx_set = set(df_tx_clean["tx_id"])
        net_tx_set = set(df_net_clean["tx_id"])
        if not net_tx_set.issubset(tx_set):
            unmatched = net_tx_set - tx_set
            tx_list = list(tx_set)
            remap = {}
            for nid in unmatched:
                if len(nid) >= 8:
                    for tid in tx_list:
                        if tid.startswith(nid) or nid.startswith(tid):
                            remap[nid] = tid
                            break
            if remap:
                df_net_clean["tx_id"] = df_net_clean["tx_id"].replace(remap)

        # Group network logs by tx_id
        grouped = df_net_clean.groupby("tx_id")

        network_features: List[Dict[str, Any]] = []

        # Pre-convert timestamps if needed
        tx_timestamps = df_tx_clean.set_index("tx_id")["timestamp"].to_dict()

        for tx_id, group in grouped:
            sorted_group = group.sort_values(by="timestamp_observed")
            earliest_row = sorted_group.iloc[0]
            latest_row = sorted_group.iloc[-1]

            first_seen = earliest_row["timestamp_observed"]
            last_seen = latest_row["timestamp_observed"]

            propagation_spread_ms = max(
                (last_seen - first_seen).total_seconds() * 1000.0,
                0.0
            )

            tx_time = tx_timestamps.get(tx_id, first_seen)
            if pd.notna(tx_time) and pd.notna(first_seen):
                conf_delay_sec = max((tx_time - first_seen).total_seconds(), 0.0)
            else:
                conf_delay_sec = 0.0

            unique_ips = sorted_group["ip_address"].unique().tolist()
            unique_asns = sorted_group["asn"].unique().tolist()
            unique_countries = sorted_group["country"].unique().tolist()

            earliest_asn = str(earliest_row.get("asn", "")).upper()
            earliest_port = int(earliest_row.get("port", 8333))
            is_tor = (earliest_asn in self.KNOWN_TOR_ASNS) or (earliest_port in (9050, 9150)) or ("tor" in str(earliest_row.get("user_agent", "")).lower())
            is_bp = earliest_asn in self.KNOWN_BULLETPROOF_ASNS

            obs_count = len(sorted_group)
            duration_sec = max((last_seen - first_seen).total_seconds(), 0.001)
            burst_velocity = obs_count / duration_sec if duration_sec > 0 else obs_count

            network_features.append({
                "tx_id": tx_id,
                "network_correlated": True,
                "observed_node_count": obs_count,
                "first_seen_timestamp": first_seen,
                "confirmation_delay_sec": round(conf_delay_sec, 2),
                "propagation_spread_ms": round(propagation_spread_ms, 1),
                "mean_latency_ms": round(float(sorted_group["latency_ms"].mean()), 2),
                "earliest_ip": earliest_row["ip_address"],
                "earliest_node_id": earliest_row["node_id"],
                "earliest_asn": earliest_asn,
                "earliest_country": str(earliest_row.get("country", "UNKNOWN")),
                "earliest_event": earliest_row["event_type"],
                "relay_ips": unique_ips,
                "relay_asns": unique_asns,
                "relay_countries": unique_countries,
                "is_tor_proxy_origin": is_tor,
                "is_bulletproof_origin": is_bp,
                "burst_velocity": round(burst_velocity, 2),
                "correlation_status": "MATCHED_NETWORK_LOGS"
            })

        df_net_summary = pd.DataFrame(network_features)

        # Merge with df_tx
        merged = pd.merge(df_tx_clean, df_net_summary, on="tx_id", how="left")

        # Fill missing values for transactions without network logs
        merged["network_correlated"] = merged["network_correlated"].fillna(False)
        merged["observed_node_count"] = merged["observed_node_count"].fillna(0).astype(int)
        merged["first_seen_timestamp"] = merged["first_seen_timestamp"].fillna(merged["timestamp"])
        merged["confirmation_delay_sec"] = merged["confirmation_delay_sec"].fillna(0.0)
        merged["propagation_spread_ms"] = merged["propagation_spread_ms"].fillna(0.0)
        merged["mean_latency_ms"] = merged["mean_latency_ms"].fillna(0.0)
        merged["earliest_ip"] = merged["earliest_ip"].fillna("N/A")
        merged["earliest_node_id"] = merged["earliest_node_id"].fillna("N/A")
        merged["earliest_asn"] = merged["earliest_asn"].fillna("N/A")
        merged["earliest_country"] = merged["earliest_country"].fillna("UNKNOWN")
        merged["earliest_event"] = merged["earliest_event"].fillna("N/A")
        merged["relay_ips"] = merged["relay_ips"].apply(lambda v: v if isinstance(v, list) else [])
        merged["relay_asns"] = merged["relay_asns"].apply(lambda v: v if isinstance(v, list) else [])
        merged["relay_countries"] = merged["relay_countries"].apply(lambda v: v if isinstance(v, list) else [])
        merged["is_tor_proxy_origin"] = merged["is_tor_proxy_origin"].fillna(False).astype(bool)
        merged["is_bulletproof_origin"] = merged["is_bulletproof_origin"].fillna(False).astype(bool)
        merged["burst_velocity"] = merged["burst_velocity"].fillna(0.0)
        merged["correlation_status"] = merged["correlation_status"].fillna("ORPHAN_TX_NO_NETWORK")

        return merged

    def compute_summary(self, correlated_df: pd.DataFrame, df_net: Optional[pd.DataFrame] = None) -> CorrelationSummary:
        """
        Computes overall correlation telemetry metrics.
        """
        total_txs = len(correlated_df)
        matched = int(correlated_df["network_correlated"].sum())
        unmatched = total_txs - matched
        rate = (matched / max(total_txs, 1)) * 100.0

        net_logs_count = len(df_net) if df_net is not None else 0
        unique_origin_ips = correlated_df[correlated_df["network_correlated"]]["earliest_ip"].nunique()
        unique_countries = correlated_df[correlated_df["network_correlated"]]["earliest_country"].nunique()
        tor_count = int(correlated_df["is_tor_proxy_origin"].sum())
        bp_count = int(correlated_df["is_bulletproof_origin"].sum())

        avg_prop_raw = correlated_df[correlated_df["network_correlated"]]["propagation_spread_ms"].mean()
        avg_conf_raw = correlated_df[correlated_df["network_correlated"]]["confirmation_delay_sec"].mean()
        avg_prop = float(avg_prop_raw) if pd.notna(avg_prop_raw) else 0.0
        avg_conf = float(avg_conf_raw) if pd.notna(avg_conf_raw) else 0.0

        return CorrelationSummary(
            total_txs=total_txs,
            matched_txs=matched,
            unmatched_txs=unmatched,
            correlation_rate_pct=round(rate, 2),
            total_network_logs=net_logs_count,
            unique_origin_ips=unique_origin_ips,
            unique_countries=unique_countries,
            tor_proxy_broadcasts=tor_count,
            bulletproof_broadcasts=bp_count,
            avg_propagation_spread_ms=round(avg_prop, 2),
            avg_confirmation_delay_sec=round(avg_conf, 2),
        )

