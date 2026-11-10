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
    generate_scenario_data
)


def test_generate_and_parse_transactions():
    df_tx, df_net = generate_scenario_data("all", n_normal=30, seed=123)
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
    df_tx, df_net = generate_scenario_data("peeling_chain", n_normal=10, seed=123)
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
    df_tx, df_net = generate_scenario_data("all", n_normal=20, seed=42)
    report = validate_forensic_data(df_tx, df_net)
    assert report.is_valid is True
    assert report.tx_count == len(df_tx)
    assert report.net_log_count == len(df_net)
    assert report.coverage_percentage > 50.0
