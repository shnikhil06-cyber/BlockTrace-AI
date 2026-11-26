"""
Tests for Advanced Analytics Charts, Wallet Profiling, and Index Alignment.
"""

from conftest import make_test_datasets
from blocktrace.correlation import CorrelationEngine
from blocktrace.ml import extract_forensic_features, AnomalyDetector, ForensicExplainer
from blocktrace.analytics import (
    build_wallet_risk_profiles,
    build_temporal_heatmap,
    build_radar_comparison,
    build_geo_broadcast_map,
    build_comparison_chart,
    build_fee_distribution_chart,
    build_pattern_sunburst,
    build_propagation_scatter,
    build_sankey_flow,
)


def _prepare_scored(seed: int = 42):
    df_tx, df_net = make_test_datasets(n_normal=30, include_anomalies=True, seed=seed)
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)
    X, meta = extract_forensic_features(df_corr)
    detector = AnomalyDetector(contamination=0.1, n_estimators=50, random_state=seed)
    scored_df = detector.fit_predict(X, meta)
    explainer = ForensicExplainer(detector.model, list(X.columns))
    explanations = explainer.explain_dataset(X, scored_df)
    exp_dict = {e["tx_id"]: e for e in explanations}
    return df_tx, df_net, X, scored_df, exp_dict


def test_wallet_profiles_and_analytics_charts():
    df_tx, df_net, X, scored_df, exp_dict = _prepare_scored()

    wallet_df = build_wallet_risk_profiles(scored_df)
    assert not wallet_df.empty
    assert "flagged_txs" in wallet_df.columns
    assert "dominant_tier" in wallet_df.columns
    assert wallet_df["max_risk_score"].is_monotonic_decreasing

    assert build_temporal_heatmap(scored_df) is not None
    assert build_geo_broadcast_map(scored_df, df_net) is not None
    assert build_fee_distribution_chart(scored_df) is not None
    assert build_pattern_sunburst(scored_df) is not None
    assert build_propagation_scatter(scored_df) is not None

    if not scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])].empty:
        assert build_radar_comparison(scored_df) is not None


def test_comparison_chart_uses_true_post_sort_features():
    _, _, X, scored_df, exp_dict = _prepare_scored()

    tx_high = scored_df.iloc[0]["tx_id"]
    tx_low = scored_df.iloc[-1]["tx_id"]

    fig = build_comparison_chart(tx_high, tx_low, scored_df, X, exp_dict)
    assert fig is not None
    assert len(fig.data) == 2

    # Confirm values match the aligned post-sort feature row rather than unsorted positional indices
    pos_high = int(scored_df.iloc[0]["_feature_row_pos"])
    true_amt_high = float(X.iloc[pos_high]["amount_btc"])
    pos_low = int(scored_df.iloc[-1]["_feature_row_pos"])
    true_amt_low = float(X.iloc[pos_low]["amount_btc"])
    expected_norm_high = true_amt_high / max(abs(true_amt_high), abs(true_amt_low), 0.001)
    assert abs(fig.data[0].y[0] - expected_norm_high) < 1e-6


def test_sankey_handles_self_change_loops_cleanly():
    _, _, _, scored_df, _ = _prepare_scored()
    # Inject a peeling transaction where the sender address also receives change
    sample = scored_df.copy()
    sample.iloc[0, sample.columns.get_loc("sender_addresses")] = ["bc1q_self_loop_addr"]
    sample.iloc[0, sample.columns.get_loc("receiver_addresses")] = ["bc1q_self_loop_addr", "bc1q_dest"]

    fig = build_sankey_flow(sample, max_txs=5)
    assert fig is not None
    links = fig.data[0].link
    for s, t in zip(links.source, links.target):
        assert s != t
