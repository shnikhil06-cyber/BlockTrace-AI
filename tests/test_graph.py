"""
Tests for Graph Construction, Analysis, and PyVis/Plotly Rendering.
"""

import pytest
import networkx as nx
from blocktrace.ingestion import generate_scenario_data
from blocktrace.correlation import CorrelationEngine
from blocktrace.ml import extract_forensic_features, AnomalyDetector
from blocktrace.graph import ForensicGraphBuilder, GraphAnalyzer, GraphVisualizer


def test_graph_construction_and_analysis():
    df_tx, df_net = generate_scenario_data("peeling_chain", n_normal=15, seed=42)
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)

    X, meta = extract_forensic_features(df_corr)
    detector = AnomalyDetector(contamination=0.1, n_estimators=30, random_state=42)
    scored = detector.fit_predict(X, meta)

    builder = ForensicGraphBuilder()
    G = builder.build_graph(scored, df_net, max_txs=50)

    assert isinstance(G, nx.DiGraph)
    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0

    analyzer = GraphAnalyzer()
    metrics = analyzer.compute_metrics(G)
    assert metrics["total_nodes"] > 0
    assert metrics["address_nodes"] > 0
    assert metrics["tx_nodes"] > 0

    # Test visualization generation
    viz = GraphVisualizer()
    fig = viz.generate_plotly_figure(G, filter_tier="ALL")
    assert fig is not None

    html = viz.generate_pyvis_html(G, filter_tier="ALL", max_nodes=25)
    assert len(html) > 500

