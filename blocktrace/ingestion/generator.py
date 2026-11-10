"""
Forensic Synthetic Dataset Generator for BlockTrace-AI.
Generates realistic Bitcoin transactions and P2P network observation logs
emulating laundering patterns, peeling chains, mixer clusters, ransomware fan-outs,
and normal baseline traffic.
"""

from typing import Tuple, List, Dict, Any
import hashlib
import random
import pandas as pd
import numpy as np


def _hash(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


def _btc_addr(prefix: str, seed: int) -> str:
    h = hashlib.sha256(f"{prefix}_{seed}".encode()).hexdigest()[:28]
    return f"bc1q{h}"


def generate_scenario_data(
    scenario: str = "all",
    n_normal: int = 120,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic transaction and network observation datasets.
    Supported scenarios: 'peeling_chain', 'mixer_tumbler', 'ransomware_fanout', 'baseline_normal', 'all'.
    """
    random.seed(seed)
    np.random.seed(seed)

    tx_list: List[Dict[str, Any]] = []
    net_list: List[Dict[str, Any]] = []

    base_time = pd.Timestamp("2026-11-10 00:00:00", tz="UTC")
    block_height_base = 850120

    # P2P Network Nodes Pool
    nodes_pool = [
        {"node_id": f"node_{i:03d}", "ip": f"198.51.100.{10+i}", "asn": f"AS{1000+i%5}", "country": c, "ua": "/Satoshi:26.0.0/"}
        for i, c in enumerate(["US", "DE", "NL", "SG", "JP", "CH", "IS", "SE", "CA", "GB", "RU", "RO"])
    ]

    # Tor/Proxy Nodes Pool
    tor_nodes_pool = [
        {"node_id": f"tor_exit_{i:02d}", "ip": f"185.220.101.{20+i}", "asn": "AS200052", "country": "NL", "ua": "/Satoshi:25.0.0(Tor)/"}
        for i in range(5)
    ]

    # Bulletproof Hosting Pool
    bulletproof_nodes_pool = [
        {"node_id": f"bp_relay_{i:02d}", "ip": f"91.240.118.{50+i}", "asn": "AS49981", "country": "RU", "ua": "/Satoshi:24.0.0/"}
        for i in range(4)
    ]

    # 1. Baseline Normal Transactions
    if scenario in ("baseline_normal", "all"):
        for i in range(n_normal):
            tx_id = _hash(f"normal_tx_{seed}_{i}")
            tx_time = base_time + pd.Timedelta(seconds=random.randint(10, 86400))
            block_h = block_height_base + int((tx_time - base_time).total_seconds() // 600)

            n_in = random.choices([1, 2, 3], weights=[0.7, 0.25, 0.05])[0]
            n_out = random.choices([1, 2], weights=[0.2, 0.8])[0]
            senders = [_btc_addr(f"user_alice_{i}", j) for j in range(n_in)]
            receivers = [_btc_addr(f"merchant_bob_{i}", j) for j in range(n_out)]

            amount = round(random.uniform(0.005, 1.8), 6)
            size_vbytes = 140 * n_in + 34 * n_out + 10
            fee_rate = round(random.uniform(8.0, 25.0), 2)  # sat/vB
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)

            tx_list.append({
                "tx_id": tx_id,
                "timestamp": tx_time,
                "block_height": block_h,
                "sender_addresses": senders,
                "receiver_addresses": receivers,
                "amount_btc": amount,
                "fee_btc": fee_btc,
                "fee_rate_sat_vb": fee_rate,
                "size_vbytes": size_vbytes,
                "is_rbf": random.choice([True, False]),
                "input_count": n_in,
                "output_count": n_out,
                "locktime": 0,
                "scenario_tag": "normal_baseline"
            })

            # Broadcast network logs: 3 to 7 nodes observe it normally
            obs_nodes = random.sample(nodes_pool, random.randint(3, 7))
            first_seen = tx_time - pd.Timedelta(seconds=random.randint(120, 600))
            for k, node in enumerate(obs_nodes):
                delay = k * random.randint(40, 150)
                obs_time = first_seen + pd.Timedelta(milliseconds=delay)
                net_list.append({
                    "log_id": f"net_{tx_id[:8]}_{k}",
                    "tx_id": tx_id,
                    "timestamp_observed": obs_time,
                    "node_id": node["node_id"],
                    "ip_address": node["ip"],
                    "port": 8333,
                    "event_type": "inv_broadcast" if k == 0 else "peer_relay",
                    "latency_ms": round(random.uniform(20.0, 120.0), 1),
                    "country": node["country"],
                    "asn": node["asn"],
                    "user_agent": node["ua"]
                })

    # 2. Peeling Chain Laundering Scenario
    # A stolen fund of 45 BTC peeled across 8 sequential transactions
    if scenario in ("peeling_chain", "all"):
        peel_time = base_time + pd.Timedelta(hours=4)
        current_amount = 45.0
        current_change_addr = _btc_addr("heist_vault", 0)

        for step in range(8):
            tx_id = _hash(f"peel_tx_{step}")
            peel_amount = round(random.uniform(0.35, 1.2), 4)  # peeled off to mule
            fee_btc = 0.00035
            size_vbytes = 224
            fee_rate = round((fee_btc * 1e8) / size_vbytes, 2)

            next_change = _btc_addr("heist_change", step + 1)
            cashout_addr = _btc_addr("mule_cashout", step)
            current_amount = round(current_amount - peel_amount - fee_btc, 4)

            tx_list.append({
                "tx_id": tx_id,
                "timestamp": peel_time,
                "block_height": block_height_base + 24 + step,
                "sender_addresses": [current_change_addr],
                "receiver_addresses": [cashout_addr, next_change],
                "amount_btc": round(peel_amount + current_amount, 4),
                "fee_btc": fee_btc,
                "fee_rate_sat_vb": fee_rate,
                "size_vbytes": size_vbytes,
                "is_rbf": True,
                "input_count": 1,
                "output_count": 2,
                "locktime": 0,
                "scenario_tag": "peeling_chain"
            })

            # Broadcast specifically originating from Tor exit nodes with very tight delay
            origin_tor = tor_nodes_pool[step % len(tor_nodes_pool)]
            first_seen = peel_time - pd.Timedelta(seconds=45)

            # Earliest observation: Tor exit node
            net_list.append({
                "log_id": f"net_peel_{step}_origin",
                "tx_id": tx_id,
                "timestamp_observed": first_seen,
                "node_id": origin_tor["node_id"],
                "ip_address": origin_tor["ip"],
                "port": 9050,
                "event_type": "inv_broadcast",
                "latency_ms": 185.0,  # High latency due to onion routing
                "country": origin_tor["country"],
                "asn": origin_tor["asn"],
                "user_agent": origin_tor["ua"]
            })

            # Normal relays observing shortly after
            for k, node in enumerate(random.sample(nodes_pool, 4)):
                net_list.append({
                    "log_id": f"net_peel_{step}_{k}",
                    "tx_id": tx_id,
                    "timestamp_observed": first_seen + pd.Timedelta(milliseconds=120 * (k + 1)),
                    "node_id": node["node_id"],
                    "ip_address": node["ip"],
                    "port": 8333,
                    "event_type": "peer_relay",
                    "latency_ms": 35.0,
                    "country": node["country"],
                    "asn": node["asn"],
                    "user_agent": node["ua"]
                })

            current_change_addr = next_change
            peel_time += pd.Timedelta(minutes=random.randint(12, 28))

    # 3. Mixer / CoinJoin Tumbler Cluster Scenario
    # 6 inputs of 1.05 BTC each, 6 equalized outputs of 1.00000000 BTC + change outputs
    if scenario in ("mixer_tumbler", "all"):
        mixer_time = base_time + pd.Timedelta(hours=9)
        for mix_round in range(3):
            tx_id = _hash(f"mixer_round_{mix_round}")
            n_participants = 6
            senders = [_btc_addr(f"mixer_in_{mix_round}", p) for p in range(n_participants)]
            # 6 equalized clean outputs + 6 change outputs = 12 outputs
            receivers = [_btc_addr(f"clean_out_{mix_round}", p) for p in range(n_participants)] + \
                        [_btc_addr(f"change_out_{mix_round}", p) for p in range(n_participants)]

            total_amt = round(n_participants * 1.05, 4)
            size_vbytes = 148 * n_participants + 34 * (n_participants * 2) + 12
            fee_btc = 0.0018
            fee_rate = round((fee_btc * 1e8) / size_vbytes, 2)

            tx_list.append({
                "tx_id": tx_id,
                "timestamp": mixer_time,
                "block_height": block_height_base + 55 + mix_round * 3,
                "sender_addresses": senders,
                "receiver_addresses": receivers,
                "amount_btc": total_amt,
                "fee_btc": fee_btc,
                "fee_rate_sat_vb": fee_rate,
                "size_vbytes": size_vbytes,
                "is_rbf": False,
                "input_count": n_participants,
                "output_count": n_participants * 2,
                "locktime": 0,
                "scenario_tag": "mixer_tumbler"
            })

            # Broadcast simultaneously across dispersed international nodes within 15ms
            first_seen = mixer_time - pd.Timedelta(seconds=18)
            for k, node in enumerate(random.sample(nodes_pool, 8)):
                net_list.append({
                    "log_id": f"net_mix_{mix_round}_{k}",
                    "tx_id": tx_id,
                    "timestamp_observed": first_seen + pd.Timedelta(milliseconds=k * 15),
                    "node_id": node["node_id"],
                    "ip_address": node["ip"],
                    "port": 8333,
                    "event_type": "inv_broadcast" if k < 2 else "peer_relay",
                    "latency_ms": 15.0,
                    "country": node["country"],
                    "asn": node["asn"],
                    "user_agent": node["ua"]
                })

            mixer_time += pd.Timedelta(minutes=45)

    # 4. Ransomware Payout & Rapid Fan-Out Scenario
    # 28.5 BTC ransom payment split into 32 micro-addresses with astronomical fee rate
    if scenario in ("ransomware_fanout", "all"):
        ransom_time = base_time + pd.Timedelta(hours=14)
        for r_case in range(2):
            tx_id = _hash(f"ransom_fanout_{r_case}")
            victim_addr = _btc_addr(f"ransom_victim_escrow_{r_case}", 1)
            fanout_targets = [_btc_addr(f"ransom_mule_pool_{r_case}", t) for t in range(28)]

            total_amt = round(random.uniform(22.0, 38.0), 4)
            size_vbytes = 148 * 1 + 34 * 28 + 10
            # Extremely high fee (350 sat/vB) for urgent block inclusion
            fee_rate = 345.0
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 6)

            tx_list.append({
                "tx_id": tx_id,
                "timestamp": ransom_time,
                "block_height": block_height_base + 84 + r_case * 2,
                "sender_addresses": [victim_addr],
                "receiver_addresses": fanout_targets,
                "amount_btc": total_amt,
                "fee_btc": fee_btc,
                "fee_rate_sat_vb": fee_rate,
                "size_vbytes": size_vbytes,
                "is_rbf": True,
                "input_count": 1,
                "output_count": len(fanout_targets),
                "locktime": 0,
                "scenario_tag": "ransomware_fanout"
            })

            # Originated from bulletproof hosting ASNs
            bp_origin = bulletproof_nodes_pool[r_case % len(bulletproof_nodes_pool)]
            first_seen = ransom_time - pd.Timedelta(seconds=12)

            net_list.append({
                "log_id": f"net_ransom_{r_case}_origin",
                "tx_id": tx_id,
                "timestamp_observed": first_seen,
                "node_id": bp_origin["node_id"],
                "ip_address": bp_origin["ip"],
                "port": 8333,
                "event_type": "inv_broadcast",
                "latency_ms": 290.0,
                "country": bp_origin["country"],
                "asn": bp_origin["asn"],
                "user_agent": bp_origin["ua"]
            })

            for k, node in enumerate(random.sample(nodes_pool, 5)):
                net_list.append({
                    "log_id": f"net_ransom_{r_case}_{k}",
                    "tx_id": tx_id,
                    "timestamp_observed": first_seen + pd.Timedelta(milliseconds=60 * (k + 1)),
                    "node_id": node["node_id"],
                    "ip_address": node["ip"],
                    "port": 8333,
                    "event_type": "peer_relay",
                    "latency_ms": 42.0,
                    "country": node["country"],
                    "asn": node["asn"],
                    "user_agent": node["ua"]
                })

            ransom_time += pd.Timedelta(hours=2)

    df_tx = pd.DataFrame(tx_list)
    df_net = pd.DataFrame(net_list)

    # Sort deterministically
    df_tx = df_tx.sort_values(by="timestamp").reset_index(drop=True)
    df_net = df_net.sort_values(by="timestamp_observed").reset_index(drop=True)

    return df_tx, df_net


def save_synthetic_data_to_disk(base_dir: str = "data"):
    """
    Saves pre-packaged scenario files to disk in both CSV and JSON formats.
    """
    import os
    import json

    os.makedirs(f"{base_dir}/sample", exist_ok=True)
    os.makedirs(f"{base_dir}/scenarios", exist_ok=True)

    # Main combined sample
    df_tx, df_net = generate_scenario_data("all", n_normal=100, seed=42)

    df_tx.to_csv(f"{base_dir}/sample/bitcoin_transactions.csv", index=False)
    df_net.to_csv(f"{base_dir}/sample/network_observations.csv", index=False)

    # Also JSON formatted
    df_tx_json = df_tx.copy()
    df_tx_json["timestamp"] = df_tx_json["timestamp"].astype(str)
    with open(f"{base_dir}/sample/bitcoin_transactions.json", "w", encoding="utf-8") as f:
        json.dump({"transactions": df_tx_json.to_dict(orient="records")}, f, indent=2)

    df_net_json = df_net.copy()
    df_net_json["timestamp_observed"] = df_net_json["timestamp_observed"].astype(str)
    with open(f"{base_dir}/sample/network_observations.json", "w", encoding="utf-8") as f:
        json.dump({"network_logs": df_net_json.to_dict(orient="records")}, f, indent=2)

    # Specific Scenario Files
    scenarios = ["peeling_chain", "mixer_tumbler", "ransomware_fanout", "baseline_normal"]
    for sc in scenarios:
        s_tx, s_net = generate_scenario_data(sc, n_normal=50, seed=101)
        s_tx_json = s_tx.copy()
        s_tx_json["timestamp"] = s_tx_json["timestamp"].astype(str)
        s_net_json = s_net.copy()
        s_net_json["timestamp_observed"] = s_net_json["timestamp_observed"].astype(str)

        scenario_payload = {
            "scenario": sc,
            "description": f"Forensic benchmark scenario for {sc}",
            "transactions": s_tx_json.to_dict(orient="records"),
            "network_logs": s_net_json.to_dict(orient="records")
        }
        with open(f"{base_dir}/scenarios/{sc}.json", "w", encoding="utf-8") as f:
            json.dump(scenario_payload, f, indent=2)


if __name__ == "__main__":
    save_synthetic_data_to_disk()
    print("Forensic sample datasets and scenarios saved successfully.")

