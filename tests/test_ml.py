"""
Tests for Machine Learning Feature Extraction, Anomaly Detection, and SHAP Explainability.
"""

import pytest
from blocktrace.ingestion import generate_scenario_data
from blocktrace.correlation import CorrelationEngine
from blocktrace.ml import extract_forensic_features, AnomalyDetector, ForensicExplainer


def test_ml_pipeline_and_shap():
    df_tx, df_net = generate_scenario_data("all", n_normal=35, seed=42)
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)

    X, meta = extract_forensic_features(df_corr)
    assert len(X) == len(df_corr)
    assert "fee_to_amount_ratio" in X.columns

    detector = AnomalyDetector(contamination=0.1, n_estimators=50, random_state=42)
    scored = detector.fit_predict(X, meta)

    assert "anomaly_score" in scored.columns
    assert "risk_tier" in scored.columns
    assert "forensic_pattern" in scored.columns
    assert scored["anomaly_score"].max() <= 100.0
    assert scored["anomaly_score"].min() >= 0.0

    # Test SHAP explainability
    explainer = ForensicExplainer(detector.model, list(X.columns))
    assert explainer.explainer is not None

    top_row_x = X.iloc[0]
    top_row_meta = scored.iloc[0]
    exp = explainer.explain_transaction(top_row_x, top_row_meta)

    assert "tx_id" in exp
    assert "top_drivers" in exp
    assert len(exp["top_drivers"]) > 0
    assert "summary_text" in exp

