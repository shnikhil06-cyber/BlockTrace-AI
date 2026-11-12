"""
Tests for Data Ingestion and Validation Modules.
"""

import os
import pandas as pd
import pytest

from blocktrace.ingestion import (
    parse_transactions,
    parse_network_logs,
    validate_forensic_data,
)
from conftest import make_test_datasets


def test_generate_and_parse_transactions():
    df_tx, df_net = make_test_datasets(n_normal=30, seed=123)
    assert not df_tx.empty
    assert "tx_id" in df_tx.columns
    assert "amount_btc" in df_tx.columns
    assert len(df_tx) >= 30

    # Save to temp csv and re-parse
    tmp_path = "/tmp/test_tx.csv"
    df_tx.to_csv(tmp_path, index=False)
    parsed = parse_transactions(tmp_path)
    assert len(parsed) == len(df_tx)
    assert "tx_id" in parsed.columns
    assert isinstance(parsed["sender_addresses"].iloc[0], list)
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def test_generate_and_parse_network_logs():
    df_tx, df_net = make_test_datasets(n_normal=10, seed=123)
    assert not df_net.empty
    assert "tx_id" in df_net.columns
    assert "ip_address" in df_net.columns

    tmp_path = "/tmp/test_net.csv"
    df_net.to_csv(tmp_path, index=False)
    parsed = parse_network_logs(tmp_path)
    assert len(parsed) == len(df_net)
    assert "latency_ms" in parsed.columns
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


def test_validation_report():
    df_tx, df_net = make_test_datasets(n_normal=20, seed=42)
    report = validate_forensic_data(df_tx, df_net)
    assert report.is_valid is True
    assert report.tx_count == len(df_tx)
    assert report.net_log_count == len(df_net)
    assert report.coverage_percentage > 50.0


def test_parse_network_logs_aliases_json_and_epoch():
    import io
    import json

    payload = {
        "logs": [
            {
                "tx_hash": "abc123",
                "observed_at": 1700000000,
                "peer_ip": "185.220.101.4",
                "cc": "de",
                "as_number": "as200052",
                "latency": 120.5,
            },
            {
                "tx_hash": "abc123",
                "observed_at": 1700000001,
                "peer_ip": None,
                "cc": None,
                "as_number": None,
                "latency": None,
            },
        ]
    }
    buf = io.BytesIO(json.dumps(payload).encode("utf-8"))
    buf.name = "obs.json"
    parsed = parse_network_logs(buf)

    assert len(parsed) == 2
    assert parsed["tx_id"].tolist() == ["abc123", "abc123"]
    assert parsed["timestamp_observed"].dt.year.iloc[0] == 2023
    assert parsed["ip_address"].iloc[0] == "185.220.101.4"
    assert parsed["ip_address"].iloc[1] == "127.0.0.1"
    assert parsed["country"].tolist() == ["DE", "UNKNOWN"]
    assert parsed["asn"].tolist() == ["AS200052", "UNKNOWN"]


def test_spaced_columns_and_tx_id_normalization():
    import io

    tx_csv = """Transaction ID,Timestamp (UTC),Amount (BTC),Fee (BTC)
0xABCDEF1234567890,2026-03-01 12:00:00,1.5,0.0001
"""
    net_csv = """Transaction Hash,Timestamp Observed,IP Address,AS Number,Country Code
abcdef1234567890,2026-03-01 11:59:00,198.51.100.5,AS15169,US
"""
    df_tx = parse_transactions(io.StringIO(tx_csv))
    df_net = parse_network_logs(io.StringIO(net_csv))

    assert df_tx["tx_id"].iloc[0] == "abcdef1234567890"
    assert df_net["tx_id"].iloc[0] == "abcdef1234567890"

    report = validate_forensic_data(df_tx, df_net)
    assert report.matched_tx_ids == 1
    assert report.coverage_percentage == 100.0



