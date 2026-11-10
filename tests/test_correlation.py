"""
Tests for Correlation Engine, Origin Tracer, and Network Clustering.
"""

import pytest
from blocktrace.ingestion import generate_scenario_data
from blocktrace.correlation import CorrelationEngine, OriginTracer, NetworkClusterer


def test_correlation_engine():
    df_tx, df_net = generate_scenario_data("all", n_normal=25, seed=42)
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)

    assert "network_correlated" in df_corr.columns
    assert "earliest_ip" in df_corr.columns
    assert "propagation_spread_ms" in df_corr.columns
    assert df_corr["network_correlated"].sum() > 0

    summary = correlator.compute_summary(df_corr, df_net)
    assert summary.matched_txs > 0
    assert summary.correlation_rate_pct > 80.0


def test_origin_tracer():
    df_tx, df_net = generate_scenario_data("ransomware_fanout", n_normal=5, seed=99)
    tracer = OriginTracer()

    target_tx = df_tx[df_tx["scenario_tag"] == "ransomware_fanout"].iloc[0]["tx_id"]
    trace_res = tracer.trace_transaction_origin(target_tx, df_net)

    assert trace_res["status"] == "ORIGIN_IDENTIFIED"
    assert trace_res["origin_ip"] is not None
    assert trace_res["origin_confidence_pct"] >= 50.0
    assert len(trace_res["timeline"]) > 0


def test_network_clusterer():
    df_tx, df_net = generate_scenario_data("all", n_normal=30, seed=42)
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)

    clusterer = NetworkClusterer()
    ip_clusters = clusterer.cluster_by_origin_ip(df_corr)
    asn_clusters = clusterer.cluster_by_asn(df_corr)

    assert len(ip_clusters) > 0
    assert len(asn_clusters) > 0
    assert "cluster_key" in ip_clusters[0]

