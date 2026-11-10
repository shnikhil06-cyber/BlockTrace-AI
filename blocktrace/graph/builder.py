"""
Multi-Modal Forensic Graph Builder for BlockTrace-AI.
Constructs directed graphs connecting Bitcoin Addresses, Transactions,
and Network Observation Nodes using NetworkX.
"""

from typing import Dict, Any, Optional
import networkx as nx
import pandas as pd


class ForensicGraphBuilder:
    """
    Constructs a directed property graph representing Bitcoin transaction flows
    and network-layer broadcast associations.
    """

    def build_graph(
        self,
        scored_tx_df: pd.DataFrame,
        df_net: Optional[pd.DataFrame] = None,
        max_txs: int = 150
    ) -> nx.DiGraph:
        """
        Builds a NetworkX DiGraph from scored transactions and network observations.
        """
        G = nx.DiGraph()

        # Limit to max_txs to preserve smooth interactive rendering
        tx_slice = scored_tx_df.head(max_txs)

        for _, tx in tx_slice.iterrows():
            tx_id = str(tx["tx_id"])
            short_tx = f"tx:{tx_id[:6]}...{tx_id[-4:]}"
            amount = float(tx.get("amount_btc", 0.0))
            fee = float(tx.get("fee_btc", 0.0))
            score = float(tx.get("anomaly_score", 0.0))
            tier = str(tx.get("risk_tier", "NORMAL"))
            pattern = str(tx.get("forensic_pattern", "BENIGN_PROFILE"))

            # Add Transaction Node
            G.add_node(
                tx_id,
                node_type="transaction",
                label=short_tx,
                full_id=tx_id,
                amount_btc=amount,
                fee_btc=fee,
                anomaly_score=score,
                risk_tier=tier,
                pattern=pattern,
                is_anomaly=bool(tx.get("is_anomaly", False))
            )

            # Add Sender Address Nodes & Edges: Sender -> Tx
            senders = tx.get("sender_addresses", [])
            if isinstance(senders, (list, tuple)):
                for sender in senders:
                    sender = str(sender).strip()
                    if sender:
                        short_addr = f"{sender[:6]}...{sender[-4:]}"
                        if sender not in G:
                            G.add_node(
                                sender,
                                node_type="address",
                                label=short_addr,
                                full_id=sender,
                                address_type="sender"
                            )
                        G.add_edge(sender, tx_id, edge_type="input_spend", amount_btc=amount / max(len(senders), 1))

            # Add Receiver Address Nodes & Edges: Tx -> Receiver
            receivers = tx.get("receiver_addresses", [])
            if isinstance(receivers, (list, tuple)):
                for receiver in receivers:
                    receiver = str(receiver).strip()
                    if receiver:
                        short_addr = f"{receiver[:6]}...{receiver[-4:]}"
                        if receiver not in G:
                            G.add_node(
                                receiver,
                                node_type="address",
                                label=short_addr,
                                full_id=receiver,
                                address_type="receiver"
                            )
                        G.add_edge(tx_id, receiver, edge_type="output_transfer", amount_btc=amount / max(len(receivers), 1))

            # Add Earliest Network IP Node & Edge: Earliest IP -> Tx
            earliest_ip = str(tx.get("earliest_ip", "N/A"))
            if earliest_ip != "N/A" and earliest_ip != "":
                ip_node_id = f"ip_{earliest_ip}"
                is_tor = bool(tx.get("is_tor_proxy_origin", False))
                is_bp = bool(tx.get("is_bulletproof_origin", False))
                asn = str(tx.get("earliest_asn", "UNKNOWN"))
                country = str(tx.get("earliest_country", "UNKNOWN"))

                if ip_node_id not in G:
                    G.add_node(
                        ip_node_id,
                        node_type="network_ip",
                        label=f"IP:{earliest_ip}",
                        full_id=earliest_ip,
                        asn=asn,
                        country=country,
                        is_tor=is_tor,
                        is_bulletproof=is_bp
                    )

                G.add_edge(
                    ip_node_id,
                    tx_id,
                    edge_type="broadcast_origin",
                    latency_ms=float(tx.get("mean_latency_ms", 0.0))
                )

        return G

