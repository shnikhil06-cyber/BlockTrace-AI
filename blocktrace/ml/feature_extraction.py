"""
Feature Engineering for BlockTrace-AI Forensic Anomaly Detection.
Combines on-chain transaction characteristics with off-chain network telemetry.
"""

from typing import List, Tuple
import pandas as pd
import numpy as np


FEATURE_COLUMNS: List[str] = [
    "amount_btc",
    "log_amount",
    "fee_btc",
    "fee_rate_sat_vb",
    "fee_to_amount_ratio",
    "input_count",
    "output_count",
    "io_ratio",
    "is_round_amount",
    "is_rbf",
    "observed_node_count",
    "propagation_spread_ms",
    "log_propagation_spread",
    "confirmation_delay_sec",
    "mean_latency_ms",
    "burst_velocity",
    "is_tor_proxy",
    "is_bulletproof",
    "unique_relay_ips_count",
    "unique_relay_asns_count",
]


def extract_forensic_features(df_correlated: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts engineered numerical feature matrix X and metadata table for forensic ML.
    """
    df = df_correlated.copy()

    # Amount & logs
    amt = df["amount_btc"].astype(float).clip(lower=0.0)
    log_amt = np.log1p(amt)

    # Fees
    fee = df["fee_btc"].astype(float).clip(lower=0.0)
    fee_rate = df["fee_rate_sat_vb"].astype(float).clip(lower=0.0)
    fee_ratio = fee / (amt + 1e-6)

    # Inputs/outputs
    in_cnt = df["input_count"].astype(float).clip(lower=1.0)
    out_cnt = df["output_count"].astype(float).clip(lower=1.0)
    io_ratio = out_cnt / in_cnt

    # Round amount heuristic (e.g. 1.0, 0.5, 0.1, 0.05, 5.0)
    def _is_round(val: float) -> float:
        for denom in [1.0, 0.5, 0.1, 0.05, 2.0, 5.0, 10.0]:
            if abs(val - round(val / denom) * denom) < 1e-5:
                return 1.0
        return 0.0

    is_round = amt.apply(_is_round)
    is_rbf = df["is_rbf"].astype(float)

    # Network metrics
    obs_cnt = df["observed_node_count"].astype(float)
    prop_spread = df["propagation_spread_ms"].astype(float).clip(lower=0.0)
    log_prop = np.log1p(prop_spread)
    conf_delay = df["confirmation_delay_sec"].astype(float).clip(lower=0.0)
    mean_lat = df["mean_latency_ms"].astype(float).clip(lower=0.0)
    burst_vel = df["burst_velocity"].astype(float).clip(lower=0.0)

    is_tor = df["is_tor_proxy_origin"].astype(float)
    is_bp = df["is_bulletproof_origin"].astype(float)

    # Count of relay IPs & ASNs
    unique_ips_cnt = df["relay_ips"].apply(lambda x: len(x) if isinstance(x, (list, set, tuple)) else 0).astype(float)
    unique_asns_cnt = df["relay_asns"].apply(lambda x: len(x) if isinstance(x, (list, set, tuple)) else 0).astype(float)

    X = pd.DataFrame({
        "amount_btc": amt,
        "log_amount": log_amt,
        "fee_btc": fee,
        "fee_rate_sat_vb": fee_rate,
        "fee_to_amount_ratio": fee_ratio,
        "input_count": in_cnt,
        "output_count": out_cnt,
        "io_ratio": io_ratio,
        "is_round_amount": is_round,
        "is_rbf": is_rbf,
        "observed_node_count": obs_cnt,
        "propagation_spread_ms": prop_spread,
        "log_propagation_spread": log_prop,
        "confirmation_delay_sec": conf_delay,
        "mean_latency_ms": mean_lat,
        "burst_velocity": burst_vel,
        "is_tor_proxy": is_tor,
        "is_bulletproof": is_bp,
        "unique_relay_ips_count": unique_ips_cnt,
        "unique_relay_asns_count": unique_asns_cnt,
    })

    # Metadata columns preserved for display & reporting
    meta = df[[
        "tx_id",
        "timestamp",
        "block_height",
        "sender_addresses",
        "receiver_addresses",
        "amount_btc",
        "fee_btc",
        "fee_rate_sat_vb",
        "input_count",
        "output_count",
        "network_correlated",
        "observed_node_count",
        "earliest_ip",
        "earliest_asn",
        "earliest_country",
        "is_tor_proxy_origin",
        "is_bulletproof_origin",
        "first_seen_timestamp",
        "propagation_spread_ms",
        "confirmation_delay_sec",
    ]].copy()

    if "scenario_tag" in df.columns:
        meta["scenario_tag"] = df["scenario_tag"]

    return X, meta
