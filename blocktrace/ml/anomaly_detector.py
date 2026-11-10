"""
Isolation Forest Anomaly Detector for BlockTrace-AI.
Detects multivariate anomalies across blockchain transactions and network telemetry.
Normalizes anomaly scores into a standardized 0-100 Forensic Risk Index.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """
    Offline Anomaly Detection model leveraging Isolation Forest on joint blockchain-network features.
    """

    def __init__(
        self,
        contamination: float = 0.08,
        n_estimators: int = 150,
        random_state: int = 42
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.feature_names: list = []

    def fit_predict(
        self,
        X: pd.DataFrame,
        meta_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Fits the Isolation Forest on feature matrix X and scores all records.
        Returns meta_df enriched with risk scores, tiers, ranks, and pattern tags.
        """
        self.feature_names = list(X.columns)

        # Handle edge cases with very few rows
        if len(X) < 2:
            results = meta_df.copy()
            results["anomaly_score"] = 10.0
            results["is_anomaly"] = False
            results["risk_tier"] = "NORMAL"
            results["risk_rank"] = 1
            results["forensic_pattern"] = "BENIGN_PROFILE"
            return results

        # Calibrate contamination if dataset is small
        effective_contamination = min(self.contamination, 0.45)
        if len(X) * effective_contamination < 1:
            effective_contamination = 1.0 / len(X)

        self.model = IsolationForest(
            contamination=effective_contamination,
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1
        )

        self.model.fit(X)

        # Raw decision function: negative values indicate anomalies, positive values normal
        # Typical range: [-0.3, 0.3]
        raw_scores = self.model.decision_function(X)
        pred_labels = self.model.predict(X)  # -1 for anomaly, 1 for inlier

        # Transform raw decision function into normalized Forensic Risk Score (0 to 100)
        # Using sigmoid/linear min-max mapping so highest anomaly = 100, normal = 0-30
        min_s = float(raw_scores.min())
        max_s = float(raw_scores.max())
        if max_s > min_s:
            # Invert: lower raw score -> higher risk score
            normalized = (max_s - raw_scores) / (max_s - min_s)
        else:
            normalized = np.zeros_like(raw_scores)

        # Scale into 0 to 100
        risk_scores = np.round(normalized * 100.0, 1)

        results = meta_df.copy()
        results["raw_anomaly_score"] = raw_scores
        results["anomaly_score"] = risk_scores
        results["is_anomaly"] = pred_labels == -1

        # Classify Risk Tier
        def _get_tier(score: float, is_anom: bool) -> str:
            if score >= 80.0:
                return "CRITICAL"
            elif score >= 65.0:
                return "HIGH"
            elif score >= 50.0:
                return "MEDIUM"
            elif score >= 35.0:
                return "LOW"
            else:
                return "NORMAL"

        results["risk_tier"] = [
            _get_tier(s, a) for s, a in zip(results["anomaly_score"], results["is_anomaly"])
        ]

        # Classify Forensic Pattern based on feature profiles
        patterns = []
        for idx in range(len(results)):
            row_meta = results.iloc[idx]
            row_x = X.iloc[idx]
            score = row_meta["anomaly_score"]

            if score < 45.0:
                patterns.append("BENIGN_PROFILE")
                continue

            # Check specific laundering/attack signatures
            out_cnt = row_x["output_count"]
            in_cnt = row_x["input_count"]
            fee_rate = row_x["fee_rate_sat_vb"]
            is_tor = row_x["is_tor_proxy"]
            is_bp = row_x["is_bulletproof"]
            prop_spread = row_x["propagation_spread_ms"]

            if out_cnt >= 15 and in_cnt <= 2:
                patterns.append("RANSOMWARE_FANOUT")
            elif in_cnt >= 4 and out_cnt >= 8 and row_x["is_round_amount"] == 1.0:
                patterns.append("COINJOIN_MIXER")
            elif in_cnt == 1 and out_cnt == 2 and (is_tor == 1.0 or row_meta["is_tor_proxy_origin"]):
                patterns.append("PEELING_CHAIN")
            elif is_bp == 1.0 or row_meta["is_bulletproof_origin"]:
                patterns.append("BULLETPROOF_RELAY_BURST")
            elif fee_rate > 150.0:
                patterns.append("HIGH_FEE_SURGE")
            elif row_x["amount_btc"] > 20.0:
                patterns.append("WHALE_TRANSFER_ANOMALY")
            else:
                patterns.append("MULTIVARIATE_NETWORK_ANOMALY")

        results["forensic_pattern"] = patterns

        # Sort by anomaly score descending and add risk rank
        results = results.sort_values(by="anomaly_score", ascending=False).reset_index(drop=True)
        results["risk_rank"] = np.arange(1, len(results) + 1)

        return results

