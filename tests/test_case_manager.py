"""
Tests for Case Manager and Report Exporter.
"""

import pytest
import pandas as pd
from blocktrace.forensic_case import ForensicCaseManager, ForensicReportExporter


def test_case_manager_and_exporter():
    case = ForensicCaseManager(
        case_id="TEST-CASE-01",
        case_title="Unit Test Investigation",
        investigator="Test Agent",
        organization="Test Unit"
    )

    ev = case.bookmark_entity(
        entity_id="tx_test_hash_123",
        entity_type="transaction",
        risk_score=94.5,
        risk_tier="CRITICAL",
        pattern="RANSOMWARE_FANOUT",
        notes="Suspect extortion payout"
    )

    assert case.is_bookmarked("tx_test_hash_123") is True
    assert len(case.notes) >= 2

    # Exporter tests
    exporter = ForensicReportExporter()
    stats = {
        "total_txs": 50,
        "matched_txs": 48,
        "correlation_rate_pct": 96.0,
        "critical_count": 2,
        "high_count": 4,
        "suspicious_volume_btc": 14.5
    }

    dummy_df = pd.DataFrame([{
        "tx_id": "tx_test_hash_123",
        "risk_rank": 1,
        "amount_btc": 10.5,
        "fee_rate_sat_vb": 250.0,
        "earliest_ip": "198.51.100.4",
        "earliest_asn": "AS49981",
        "earliest_country": "RU",
        "risk_tier": "CRITICAL",
        "anomaly_score": 94.5,
        "forensic_pattern": "RANSOMWARE_FANOUT"
    }])

    md_report = exporter.generate_markdown_report(case, stats, dummy_df)
    assert "# FORENSIC AUDIT DOSSIER" in md_report
    assert "tx_test_hash_123" in md_report

    html_report = exporter.generate_html_report(case, stats, dummy_df)
    assert "<!DOCTYPE html>" in html_report
    assert "TEST-CASE-01" in html_report

    json_report = exporter.export_json(case, stats, dummy_df)
    assert "TEST-CASE-01" in json_report

