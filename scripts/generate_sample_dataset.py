"""
Generate a 1000-entry realistic Bitcoin forensic dataset for BlockTrace-AI testing.
Generates:
  1. test_data/transactions_1000.csv (1000 Bitcoin transactions with realistic forensic patterns)
  2. test_data/network_logs_1000.csv (Matching P2P network observation logs with multi-hop propagation)
"""

import os
import random
import hashlib
from datetime import datetime, timedelta, timezone
import pandas as pd

random.seed(42)

# Forensic address pools
BENIGN_SENDERS = [
    f"bc1q{hashlib.sha256(f'benign_s_{i}'.encode()).hexdigest()[:38]}" for i in range(150)
]
BENIGN_RECEIVERS = [
    f"bc1q{hashlib.sha256(f'benign_r_{i}'.encode()).hexdigest()[:38]}" for i in range(200)
]
WHALE_WALLETS = [
    f"3Whale{hashlib.sha256(f'whale_{i}'.encode()).hexdigest()[:28]}" for i in range(15)
]
MIXER_WALLETS = [
    f"1Mixer{hashlib.sha256(f'mixer_{i}'.encode()).hexdigest()[:28]}" for i in range(25)
]
DARKNET_WALLETS = [
    f"1Dark{hashlib.sha256(f'dark_{i}'.encode()).hexdigest()[:29]}" for i in range(20)
]

# ASNs and Geo data
BENIGN_ASNS = [
    ("AS13335", "US", "Cloudflare"),
    ("AS15169", "US", "Google LLC"),
    ("AS16509", "US", "Amazon.com"),
    ("AS8075", "US", "Microsoft"),
    ("AS3320", "DE", "Deutsche Telekom"),
    ("AS12322", "FR", "Free SAS"),
    ("AS25160", "JP", "KDDI"),
    ("AS4713", "JP", "NTT Communications"),
    ("AS2856", "GB", "British Telecom"),
    ("AS6830", "NL", "Liberty Global"),
    ("AS13030", "CH", "Init7"),
    ("AS55836", "SG", "Reliance Jio"),
]

TOR_EXIT_ASNS = [
    ("AS9009", "DE", "M247 Europe"),
    ("AS200052", "SC", "Bulletproof Host"),
    ("AS60729", "NL", "Tor Relay Collective"),
    ("AS202425", "RU", "CyberPrivacy Ltd"),
]

USER_AGENTS = [
    "/Satoshi:26.0.0/",
    "/Satoshi:25.1.0/",
    "/BitcoinCore:27.0.0/",
    "/Satoshi:24.0.1/",
    "/Knots:25.1.knots20231115/",
]

def make_tx_id(seed_str: str) -> str:
    return hashlib.sha256(seed_str.encode()).hexdigest()

def make_ip(seed: int, is_tor: bool = False) -> str:
    if is_tor:
        return f"185.220.{100 + (seed % 30)}.{seed % 250 + 1}"
    return f"{(seed * 17) % 200 + 20}.{(seed * 31) % 250 + 1}.{(seed * 7) % 250 + 1}.{seed % 250 + 1}"

def generate_1000_dataset():
    os.makedirs("test_data", exist_ok=True)
    base_time = datetime(2026, 4, 1, 10, 0, 0, tzinfo=timezone.utc)

    transactions = []
    network_logs = []
    net_log_id = 1

    for i in range(1, 1001):
        tx_time = base_time + timedelta(minutes=i * 4 + random.randint(0, 180))
        block_height = 840000 + (i // 7)

        # Distribute forensic archetypes:
        # 1-780: Benign organic payments (78%)
        # 781-840: CoinJoin / High-fanout Mixing (6%)
        # 841-890: Rapid UTXO Sweeps & Consolidations (5%)
        # 891-940: High-Value Peeling Chains (5%)
        # 941-975: Dusting Attacks (3.5%)
        # 976-1000: Darknet / Tor Bulletproof Relays (2.5%)

        if i <= 780:
            # Benign
            senders = [random.choice(BENIGN_SENDERS)]
            receivers = [random.choice(BENIGN_RECEIVERS), random.choice(BENIGN_SENDERS)]
            amount = round(random.uniform(0.015, 3.85), 6)
            size_vbytes = random.randint(140, 260)
            fee_rate = round(random.uniform(12.0, 38.0), 1)
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = random.random() < 0.25
            is_tor = False
            asn_pool = BENIGN_ASNS
            hop_count = random.randint(2, 4)

        elif i <= 840:
            # CoinJoin / Equal-output mixing
            n_in = random.randint(6, 12)
            n_out = random.randint(6, 12)
            senders = random.sample(BENIGN_SENDERS + MIXER_WALLETS, n_in)
            denom = random.choice([0.05, 0.1, 0.5])
            receivers = [random.choice(MIXER_WALLETS) for _ in range(n_out)]
            amount = round(denom * n_out, 6)
            size_vbytes = 100 + n_in * 68 + n_out * 31
            fee_rate = round(random.uniform(55.0, 120.0), 1)
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = True
            is_tor = random.random() < 0.6
            asn_pool = TOR_EXIT_ASNS if is_tor else BENIGN_ASNS
            hop_count = random.randint(3, 5)

        elif i <= 890:
            # Rapid UTXO Consolidation / Sweep
            n_in = random.randint(10, 20)
            senders = random.sample(BENIGN_SENDERS, n_in)
            receivers = [random.choice(WHALE_WALLETS)]
            amount = round(random.uniform(12.0, 65.0), 4)
            size_vbytes = 80 + n_in * 68 + 34
            fee_rate = round(random.uniform(70.0, 160.0), 1)
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = False
            is_tor = random.random() < 0.4
            asn_pool = TOR_EXIT_ASNS if is_tor else BENIGN_ASNS
            hop_count = random.randint(2, 4)

        elif i <= 940:
            # High-Value Peeling Chain
            senders = [random.choice(WHALE_WALLETS)]
            peel_amt = round(random.uniform(0.1, 1.5), 4)
            change_amt = round(random.uniform(45.0, 180.0), 4)
            receivers = [random.choice(BENIGN_RECEIVERS), senders[0]]
            amount = round(peel_amt + change_amt, 4)
            size_vbytes = 224
            fee_rate = round(random.uniform(25.0, 60.0), 1)
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = True
            is_tor = False
            asn_pool = BENIGN_ASNS
            hop_count = random.randint(2, 3)

        elif i <= 975:
            # Dusting Attack
            senders = [random.choice(DARKNET_WALLETS)]
            n_out = random.randint(8, 18)
            receivers = random.sample(BENIGN_RECEIVERS, n_out)
            dust_amt = 0.00000546
            amount = round(dust_amt * n_out, 8)
            size_vbytes = 68 + n_out * 34
            fee_rate = round(random.uniform(110.0, 240.0), 1) # very high fee density
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = False
            is_tor = True
            asn_pool = TOR_EXIT_ASNS
            hop_count = random.randint(3, 5)

        else:
            # Darknet / Tor Bulletproof Broadcast
            senders = [random.choice(DARKNET_WALLETS)]
            receivers = [random.choice(DARKNET_WALLETS), random.choice(MIXER_WALLETS)]
            amount = round(random.uniform(4.5, 38.0), 4)
            size_vbytes = random.randint(220, 480)
            fee_rate = round(random.uniform(85.0, 210.0), 1)
            fee_btc = round((fee_rate * size_vbytes) / 1e8, 8)
            is_rbf = True
            is_tor = True
            asn_pool = TOR_EXIT_ASNS
            hop_count = random.randint(3, 5)

        tx_id = make_tx_id(f"blocktrace_tx_{i}_{amount}")

        transactions.append({
            "tx_id": tx_id,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "block_height": block_height,
            "sender_addresses": "|".join(senders),
            "receiver_addresses": "|".join(receivers),
            "amount_btc": amount,
            "fee_btc": fee_btc,
            "fee_rate_sat_vb": fee_rate,
            "size_vbytes": size_vbytes,
            "input_count": len(senders),
            "output_count": len(receivers),
            "locktime": 0 if not is_rbf else block_height - 1,
            "is_rbf": is_rbf,
        })

        # Generate P2P network telemetry observations
        # Hop 0 is the broadcast origin
        for hop in range(hop_count):
            hop_asn_info = random.choice(asn_pool) if hop == 0 else random.choice(BENIGN_ASNS)
            hop_asn, hop_country, _ = hop_asn_info
            hop_ip = make_ip(i * 13 + hop * 97, is_tor=(hop == 0 and is_tor))
            hop_delta_ms = 0 if hop == 0 else (hop * random.randint(85, 240) + random.randint(5, 45))
            hop_latency = round(random.uniform(15.0, 75.0) if hop > 0 else (random.uniform(180.0, 420.0) if is_tor else random.uniform(25.0, 85.0)), 1)
            
            event_type = "inv_broadcast" if hop == 0 else ("peer_relay" if hop < hop_count - 1 else "mempool_accept")

            network_logs.append({
                "log_id": f"net_{net_log_id:06d}",
                "tx_id": tx_id,
                "timestamp_observed": (tx_time + timedelta(milliseconds=hop_delta_ms)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " UTC",
                "ip_address": hop_ip,
                "port": 8333,
                "event_type": event_type,
                "latency_ms": hop_latency,
                "country": hop_country,
                "asn": hop_asn,
                "user_agent": random.choice(USER_AGENTS),
            })
            net_log_id += 1

    df_tx = pd.DataFrame(transactions)
    df_net = pd.DataFrame(network_logs)

    df_tx.to_csv("test_data/transactions_1000.csv", index=False)
    df_net.to_csv("test_data/network_logs_1000.csv", index=False)

    print(f"Generated {len(df_tx)} transactions in test_data/transactions_1000.csv")
    print(f"Generated {len(df_net)} network observations in test_data/network_logs_1000.csv")

if __name__ == "__main__":
    generate_1000_dataset()
