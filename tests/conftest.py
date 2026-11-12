"""
Pytest test fixtures generating minimal in-memory DataFrames for unit tests.
"""

from datetime import datetime, timedelta, timezone
import numpy as np
import pandas as pd


def make_test_datasets(n_normal: int = 25, include_anomalies: bool = True, seed: int = 42):
    """Build deterministic in-memory transaction and network DataFrames for unit tests."""
    rng = np.random.default_rng(seed)
    base_time = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)

    tx_rows = []
    net_rows = []

    for i in range(n_normal):
        tx_id = f"tx_norm_{i:04d}"
        ts = base_time + timedelta(minutes=i * 2)
        in_cnt = int(rng.integers(1, 3))
        out_cnt = int(rng.integers(1, 3))
        size_vb = 180 + in_cnt * 60 + out_cnt * 34
        fee_rate = float(rng.uniform(12.0, 35.0))
        fee_btc = round((fee_rate * size_vb) / 1e8, 8)
        tx_rows.append({
            "tx_id": tx_id,
            "timestamp": ts,
            "block_height": 840000 + i,
            "sender_addresses": [f"bc1q_norm_s_{i}_{k}" for k in range(in_cnt)],
            "receiver_addresses": [f"bc1q_norm_r_{i}_{k}" for k in range(out_cnt)],
            "amount_btc": round(float(rng.uniform(0.05, 1.5)), 6),
            "fee_btc": fee_btc,
            "fee_rate_sat_vb": round(fee_rate, 2),
            "size_vbytes": size_vb,
            "is_rbf": False,
            "input_count": in_cnt,
            "output_count": out_cnt,
            "locktime": 0,
            "scenario_tag": "normal",
        })
        for hop in range(3):
            obs_ts = ts - timedelta(seconds=120) + timedelta(milliseconds=hop * 140)
            net_rows.append({
                "log_id": f"log_{tx_id}_{hop}",
                "tx_id": tx_id,
                "timestamp_observed": obs_ts,
                "node_id": f"node_{hop}",
                "ip_address": f"198.51.100.{10 + (i % 5) + hop}",
                "port": 8333,
                "event_type": "inv_broadcast" if hop == 0 else "peer_relay",
                "latency_ms": round(float(rng.uniform(25.0, 90.0)), 2),
                "asn": "AS15169" if hop == 0 else "AS13335",
                "country": "US" if hop == 0 else "DE",
                "user_agent": "/Satoshi:26.0.0/",
            })

    if include_anomalies:
        anom_specs = [
            ("tx_anom_peel_01", 45.0, 120.0, 1, 2, "185.220.101.4", "AS200052", "DE", 9050, "peeling_chain"),
            ("tx_anom_peel_02", 44.5, 115.0, 1, 2, "185.220.101.4", "AS200052", "DE", 9050, "peeling_chain"),
            ("tx_anom_ransom_01", 12.5, 250.0, 1, 30, "45.142.120.10", "AS49981", "RU", 8333, "ransomware_fanout"),
            ("tx_anom_mixer_01", 3.2, 65.0, 18, 18, "91.215.85.12", "AS60729", "NL", 9050, "mixer_tumbler"),
        ]
        for idx, (tx_id, amt, fee_rate, in_c, out_c, ip, asn, cc, port, tag) in enumerate(anom_specs):
            ts = base_time + timedelta(minutes=(n_normal + idx) * 2)
            size_vb = 200 + in_c * 68 + out_c * 34
            fee_btc = round((fee_rate * size_vb) / 1e8, 8)
            tx_rows.append({
                "tx_id": tx_id,
                "timestamp": ts,
                "block_height": 840100 + idx,
                "sender_addresses": [f"bc1q_anom_s_{idx}_{k}" for k in range(in_c)],
                "receiver_addresses": [f"bc1q_anom_r_{idx}_{k}" for k in range(out_c)],
                "amount_btc": amt,
                "fee_btc": fee_btc,
                "fee_rate_sat_vb": fee_rate,
                "size_vbytes": size_vb,
                "is_rbf": True,
                "input_count": in_c,
                "output_count": out_c,
                "locktime": 0,
                "scenario_tag": tag,
            })
            for hop in range(4):
                obs_ts = ts - timedelta(seconds=240) + timedelta(milliseconds=hop * 45)
                net_rows.append({
                    "log_id": f"log_{tx_id}_{hop}",
                    "tx_id": tx_id,
                    "timestamp_observed": obs_ts,
                    "node_id": f"anom_node_{hop}",
                    "ip_address": ip if hop == 0 else f"203.0.113.{20 + hop}",
                    "port": port if hop == 0 else 8333,
                    "event_type": "inv_broadcast" if hop == 0 else "peer_relay",
                    "latency_ms": round(180.0 + hop * 20.0, 2),
                    "asn": asn if hop == 0 else "AS13335",
                    "country": cc if hop == 0 else "NL",
                    "user_agent": "/TorRelay:0.4/" if port == 9050 else "/Satoshi:25.0.0/",
                })

    df_tx = pd.DataFrame(tx_rows)
    df_net = pd.DataFrame(net_rows)
    return df_tx, df_net

