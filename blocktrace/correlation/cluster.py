"""
Network Clustering and Relationship Mapping for BlockTrace-AI.
Groups transactions sharing common broadcast IPs, ASNs, or synchronized burst windows.
"""

from typing import Dict, Any, List
import pandas as pd


class NetworkClusterer:
    """
    Identifies clusters of transactions connected by network observations.
    """

    def cluster_by_origin_ip(self, correlated_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Groups transactions by their earliest broadcast IP address.
        """
        valid = correlated_df[
            (correlated_df["network_correlated"]) &
            (correlated_df["earliest_ip"] != "N/A")
        ]

        clusters = []
        for ip, group in valid.groupby("earliest_ip"):
            if len(group) >= 1:
                total_btc = float(group["amount_btc"].sum())
                tx_ids = group["tx_id"].tolist()
                earliest_country = group.iloc[0]["earliest_country"]
                earliest_asn = group.iloc[0]["earliest_asn"]
                is_tor = bool(group.iloc[0]["is_tor_proxy_origin"])
                is_bp = bool(group.iloc[0]["is_bulletproof_origin"])

                clusters.append({
                    "cluster_type": "ORIGIN_IP",
                    "cluster_key": ip,
                    "tx_count": len(group),
                    "total_amount_btc": round(total_btc, 4),
                    "country": earliest_country,
                    "asn": earliest_asn,
                    "is_anonymizer": is_tor or is_bp,
                    "risk_flag": "HIGH" if (is_tor or is_bp or len(group) > 4) else "LOW",
                    "tx_ids": tx_ids
                })

        clusters.sort(key=lambda x: (x["is_anonymizer"], x["tx_count"], x["total_amount_btc"]), reverse=True)
        return clusters

    def cluster_by_asn(self, correlated_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Groups transactions by Autonomous System Number (ASN).
        """
        valid = correlated_df[
            (correlated_df["network_correlated"]) &
            (correlated_df["earliest_asn"] != "N/A")
        ]

        clusters = []
        for asn, group in valid.groupby("earliest_asn"):
            clusters.append({
                "cluster_type": "ASN",
                "cluster_key": asn,
                "tx_count": len(group),
                "total_amount_btc": round(float(group["amount_btc"].sum()), 4),
                "unique_ips": int(group["earliest_ip"].nunique()),
                "countries": group["earliest_country"].unique().tolist(),
                "tx_ids": group["tx_id"].tolist()
            })

        clusters.sort(key=lambda x: x["tx_count"], reverse=True)
        return clusters

