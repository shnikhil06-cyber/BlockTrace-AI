"""
Explainable AI (XAI) for BlockTrace-AI Forensic Alerts using SHAP.
Generates local Shapley feature contributions, evidence rationale,
and narrative explanations for cybercrime investigators.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import shap


# Human-friendly feature labels and descriptions
FEATURE_LABELS = {
    "amount_btc": "Transaction Volume (BTC)",
    "log_amount": "Log Volume Scale",
    "fee_btc": "Absolute Miner Fee (BTC)",
    "fee_rate_sat_vb": "Fee Density (sat/vB)",
    "fee_to_amount_ratio": "Fee-to-Principal Ratio",
    "input_count": "Input Count (Fan-in)",
    "output_count": "Output Count (Fan-out)",
    "io_ratio": "Fan-out / Fan-in Disparity",
    "is_round_amount": "Equalized/Round Value Pattern",
    "is_rbf": "Replace-By-Fee Flag",
    "observed_node_count": "P2P Observing Nodes",
    "propagation_spread_ms": "P2P Propagation Spread (ms)",
    "log_propagation_spread": "Log Propagation Latency",
    "confirmation_delay_sec": "Confirmation Delay (s)",
    "mean_latency_ms": "Average Node Relay Latency (ms)",
    "burst_velocity": "Broadcast Burst Velocity (tx/s)",
    "is_tor_proxy": "Tor / Anonymizer Origin Flag",
    "is_bulletproof": "Bulletproof Hosting ASN Flag",
    "unique_relay_ips_count": "Distinct Relay IPs",
    "unique_relay_asns_count": "Distinct Autonomous Systems (ASNs)",
}


class ForensicExplainer:
    """
    Computes SHAP explanations and generates evidence-based forensic rationale.
    """

    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer: Optional[shap.TreeExplainer] = None
        self._init_explainer()

    def _init_explainer(self):
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            self.explainer = None

    def _build_explanation_record(
        self,
        X_row: pd.Series,
        meta_row: pd.Series,
        shap_vals: np.ndarray,
    ) -> Dict[str, Any]:
        """Constructs a structured SHAP attribution and narrative record from precomputed values."""
        impacts = []
        for feat_name, shap_val in zip(self.feature_names, shap_vals):
            raw_val = X_row.get(feat_name, 0.0)
            impacts.append({
                "feature": feat_name,
                "label": FEATURE_LABELS.get(feat_name, feat_name),
                "value": float(raw_val),
                "shap_impact": float(shap_val),
                "abs_impact": abs(float(shap_val)),
            })

        impacts.sort(key=lambda x: x["abs_impact"], reverse=True)
        top_drivers = impacts[:5]

        score = float(meta_row.get("anomaly_score", 50.0))
        tier = str(meta_row.get("risk_tier", "NORMAL"))
        pattern = str(meta_row.get("forensic_pattern", "BENIGN_PROFILE"))
        tx_id = str(meta_row.get("tx_id", "Unknown"))

        narrative_bullets: List[str] = []

        if tier in ("CRITICAL", "HIGH", "MEDIUM"):
            if pattern == "DUSTING_ATTACK":
                narrative_bullets.append(
                    f"Dusting fingerprint: micro-principal ({float(X_row.get('amount_btc', 0)):.8f} BTC) split across {int(X_row.get('output_count', 0))} targets to deanonymize UTXO clusters."
                )
            elif pattern == "RANSOMWARE_FANOUT":
                narrative_bullets.append(
                    f"Rapid fan-out detected: {int(X_row.get('input_count', 1))} input(s) split into {int(X_row.get('output_count', 0))} outputs, consistent with automated extortion distribution."
                )
            elif pattern == "COINJOIN_MIXER":
                narrative_bullets.append(
                    f"CoinJoin / Tumbler signature: {int(X_row.get('input_count', 0))} inputs unified into {int(X_row.get('output_count', 0))} outputs, obfuscating UTXO provenance."
                )
            elif pattern == "UTXO_CONSOLIDATION_SWEEP":
                narrative_bullets.append(
                    f"High fan-in UTXO sweep: {int(X_row.get('input_count', 0))} fragmented inputs consolidated into {int(X_row.get('output_count', 1))} destination address(es)."
                )
            elif pattern == "PEELING_CHAIN":
                narrative_bullets.append(
                    "Peeling chain flow: single-input dual-output structure siphoning funds while passing high-value residual change forward."
                )
            elif pattern == "BULLETPROOF_RELAY_BURST":
                narrative_bullets.append(
                    f"Origin traced to high-risk bulletproof hosting ASN ({meta_row.get('earliest_asn')}) from IP {meta_row.get('earliest_ip')}."
                )
            elif pattern == "HIGH_FEE_SURGE":
                narrative_bullets.append(
                    f"Urgent priority fee surge ({float(X_row.get('fee_rate_sat_vb', 0)):.1f} sat/vB) typical of rapid illicit fund evacuation."
                )
            elif pattern == "WHALE_TRANSFER_ANOMALY":
                narrative_bullets.append(
                    f"High-magnitude principal movement ({float(X_row.get('amount_btc', 0)):.4f} BTC) far above baseline ledger volume."
                )

            if float(X_row.get("fee_rate_sat_vb", 0)) > 100 and pattern != "HIGH_FEE_SURGE":
                narrative_bullets.append(
                    f"Abnormally high fee density: {float(X_row.get('fee_rate_sat_vb', 0)):.1f} sat/vB paid for priority block inclusion."
                )
            if float(X_row.get("is_tor_proxy", 0)) == 1.0 or bool(meta_row.get("is_tor_proxy_origin", False)):
                narrative_bullets.append(
                    f"Transaction broadcast originated from known Tor exit/anonymizer node ({meta_row.get('earliest_ip')})."
                )
            if bool(meta_row.get("network_correlated", False)) and float(X_row.get("propagation_spread_ms", 0)) < 50:
                narrative_bullets.append(
                    f"Sub-50ms synchronized global network broadcast burst ({float(X_row.get('propagation_spread_ms', 0)):.1f} ms spread)."
                )

            if not narrative_bullets:
                top_1 = top_drivers[0]
                top_2 = top_drivers[1] if len(top_drivers) > 1 else top_1
                narrative_bullets.append(
                    f"Multivariate deviation driven by {top_1['label']} (val: {top_1['value']:.2f}) and {top_2['label']} (val: {top_2['value']:.2f})."
                )
        else:
            narrative_bullets.append(
                "Transaction matches normal baseline peer propagation and standard on-chain fee/output distribution."
            )

        summary_text = (
            f"Alert Level: {tier} (Forensic Risk: {score:.1f}/100) — Pattern: {pattern.replace('_', ' ')}. "
            + " ".join(narrative_bullets)
        )

        return {
            "tx_id": tx_id,
            "risk_score": score,
            "risk_tier": tier,
            "pattern": pattern,
            "top_drivers": top_drivers,
            "all_impacts": impacts,
            "narrative_bullets": narrative_bullets,
            "summary_text": summary_text,
            "investigator_disclaimer": "Risk scores are heuristic indicators for prioritizing forensic triage, not definitive legal proof of illicit activity.",
        }

    def explain_transaction(
        self,
        X_row: pd.Series,
        meta_row: pd.Series
    ) -> Dict[str, Any]:
        """
        Computes SHAP feature importance for a single transaction and generates
        a human-readable forensic explanation narrative.
        """
        row_df = pd.DataFrame([X_row[self.feature_names]])
        vals = np.zeros(len(self.feature_names))
        if self.explainer is not None:
            try:
                raw_shap = self.explainer.shap_values(row_df)
                if isinstance(raw_shap, list):
                    vals = np.array(raw_shap[0][0])
                elif isinstance(raw_shap, np.ndarray):
                    vals = raw_shap[0] if raw_shap.ndim > 1 else raw_shap
            except Exception:
                pass
        return self._build_explanation_record(X_row, meta_row, vals)

    @staticmethod
    def generate_waterfall_figure(exp: Dict[str, Any]):
        """
        Generates an interactive Plotly Waterfall figure of SHAP feature contributions.
        """
        import plotly.graph_objects as go

        drivers = exp.get("top_drivers", [])
        if not drivers:
            return None

        labels = [d["label"] for d in drivers]
        impacts = [d["shap_impact"] for d in drivers]
        texts = [f"{v:+.3f}" for v in impacts]

        fig = go.Figure(go.Waterfall(
            name="SHAP Impact",
            orientation="v",
            measure=["relative"] * len(drivers),
            x=labels,
            textposition="outside",
            text=texts,
            y=impacts,
            decreasing={"marker": {"color": "#ef4444"}},
            increasing={"marker": {"color": "#10b981"}},
            totals={"marker": {"color": "#38bdf8"}},
            connector={"line": {"color": "#475569", "width": 1.5, "dash": "dot"}},
        ))

        fig.update_layout(
            title=dict(
                text="<b>SHAP Feature Attribution Waterfall (Decision Shift)</b>",
                font=dict(size=14, color="#f8fafc")
            ),
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            font_color="#f8fafc",
            yaxis=dict(gridcolor="#1e293b", title="Shapley Attribution Value"),
            xaxis=dict(tickangle=-25),
            margin=dict(t=40, b=60, l=40, r=40),
            showlegend=False
        )

        return fig

    def explain_dataset(
        self,
        X: pd.DataFrame,
        scored_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Batch computes forensic explanations for all transactions using true X alignment
        and vectorized SHAP tree evaluation.
        """
        if scored_df.empty:
            return []

        if "_feature_row_pos" in scored_df.columns:
            positions = scored_df["_feature_row_pos"].astype(int).tolist()
            X_aligned = X.iloc[positions].reset_index(drop=True)
        else:
            X_aligned = X.iloc[:len(scored_df)].reset_index(drop=True)

        shap_matrix = np.zeros((len(scored_df), len(self.feature_names)))
        if self.explainer is not None:
            try:
                raw_shap = self.explainer.shap_values(X_aligned[self.feature_names])
                if isinstance(raw_shap, list):
                    shap_matrix = np.asarray(raw_shap[0])
                elif isinstance(raw_shap, np.ndarray):
                    shap_matrix = raw_shap if raw_shap.ndim > 1 else raw_shap.reshape(1, -1)
            except Exception:
                pass

        explanations = []
        for idx in range(len(scored_df)):
            explanations.append(
                self._build_explanation_record(
                    X_aligned.iloc[idx],
                    scored_df.iloc[idx],
                    shap_matrix[idx],
                )
            )
        return explanations

