"""
Data Quality and Validation for Blockchain Records and Network Logs.
Provides forensic integrity checks, anomaly pre-screening, and schema verification.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from blocktrace.ingestion.parsers import normalize_tx_id


@dataclass
class DataQualityReport:
    is_valid: bool
    tx_count: int = 0
    net_log_count: int = 0
    unique_tx_ids_tx: int = 0
    unique_tx_ids_net: int = 0
    matched_tx_ids: int = 0
    coverage_percentage: float = 0.0
    unique_senders: int = 0
    unique_receivers: int = 0
    unique_ips: int = 0
    unique_asns: int = 0
    unique_nodes: int = 0
    temporal_span_hours: float = 0.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "tx_count": self.tx_count,
            "net_log_count": self.net_log_count,
            "coverage_percentage": round(self.coverage_percentage, 2),
            "matched_tx_ids": self.matched_tx_ids,
            "unique_ips": self.unique_ips,
            "unique_asns": self.unique_asns,
            "temporal_span_hours": round(self.temporal_span_hours, 2),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
        }


def validate_forensic_data(
    df_tx: pd.DataFrame,
    df_net: pd.DataFrame = None
) -> DataQualityReport:
    """
    Validates ingested transaction records and optional network logs.
    Identifies missing data, temporal anomalies, and cross-source linkage.
    """
    warnings = []
    errors = []

    if df_tx is None or df_tx.empty:
        return DataQualityReport(is_valid=False, errors=["Transaction dataframe is empty or None."])

    if "tx_id" not in df_tx.columns:
        errors.append("Transactions table missing mandatory column 'tx_id'.")

    tx_count = len(df_tx)
    unique_tx_ids_tx = df_tx["tx_id"].nunique()
    if unique_tx_ids_tx < tx_count:
        warnings.append(f"Found {tx_count - unique_tx_ids_tx} duplicate transaction hashes in transaction dataset.")

    # Address checks
    all_senders = set()
    for senders in df_tx.get("sender_addresses", []):
        if isinstance(senders, (list, tuple)):
            all_senders.update(senders)
    all_receivers = set()
    for receivers in df_tx.get("receiver_addresses", []):
        if isinstance(receivers, (list, tuple)):
            all_receivers.update(receivers)

    # Temporal span
    span_hours = 0.0
    if "timestamp" in df_tx.columns and not df_tx["timestamp"].empty:
        min_t = df_tx["timestamp"].min()
        max_t = df_tx["timestamp"].max()
        if pd.notna(min_t) and pd.notna(max_t):
            span_hours = (max_t - min_t).total_seconds() / 3600.0

    net_log_count = 0
    unique_tx_ids_net = 0
    matched_tx_ids = 0
    coverage_pct = 0.0
    unique_ips = 0
    unique_asns = 0
    unique_nodes = 0

    if df_net is not None and not df_net.empty:
        net_log_count = len(df_net)
        if "tx_id" not in df_net.columns:
            errors.append("Network logs missing mandatory column 'tx_id'.")
        else:
            tx_series_norm = df_tx["tx_id"].apply(normalize_tx_id)
            net_series_norm = df_net["tx_id"].apply(normalize_tx_id)

            unique_tx_ids_net = net_series_norm.nunique()
            tx_set = set(tx_series_norm)
            net_set = set(net_series_norm)
            matched = tx_set.intersection(net_set)
            matched_tx_ids = len(matched)

            # Check prefix/substring matching if direct set intersection is incomplete
            if matched_tx_ids < len(tx_set) and len(net_set - tx_set) > 0:
                unmatched_net = net_set - tx_set
                tx_list = list(tx_set)
                prefix_matched_txs = set()
                for nid in unmatched_net:
                    if len(nid) >= 8:
                        for tid in tx_list:
                            if tid.startswith(nid) or nid.startswith(tid):
                                prefix_matched_txs.add(tid)
                                break
                matched_tx_ids = len(matched.union(prefix_matched_txs))

            coverage_pct = (matched_tx_ids / max(unique_tx_ids_tx, 1)) * 100.0

            if coverage_pct < 50.0:
                warnings.append(
                    f"Low network correlation coverage: only {coverage_pct:.1f}% of transactions have matching network logs."
                )

            unmatched_net = len(net_set - tx_set)
            if unmatched_net > 0 and coverage_pct < 100.0:
                warnings.append(f"{unmatched_net} network logs reference transaction IDs not present in blockchain dataset.")

            if "ip_address" in df_net.columns:
                unique_ips = df_net["ip_address"].nunique()
            if "asn" in df_net.columns:
                unique_asns = df_net["asn"].nunique()
            if "node_id" in df_net.columns:
                unique_nodes = df_net["node_id"].nunique()
    else:
        warnings.append("No network observation logs provided. Analysis will rely solely on on-chain heuristics.")

    is_valid = len(errors) == 0

    return DataQualityReport(
        is_valid=is_valid,
        tx_count=tx_count,
        net_log_count=net_log_count,
        unique_tx_ids_tx=unique_tx_ids_tx,
        unique_tx_ids_net=unique_tx_ids_net,
        matched_tx_ids=matched_tx_ids,
        coverage_percentage=coverage_pct,
        unique_senders=len(all_senders),
        unique_receivers=len(all_receivers),
        unique_ips=unique_ips,
        unique_asns=unique_asns,
        unique_nodes=unique_nodes,
        temporal_span_hours=span_hours,
        warnings=warnings,
        errors=errors
    )

