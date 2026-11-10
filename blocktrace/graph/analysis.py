"""
Graph Topology and Path Analysis for BlockTrace-AI.
Extracts network centrality metrics, traces laundering flows, detects peeling chains,
and finds transaction paths between suspicious wallets.
"""

from typing import Dict, Any, List, Optional
import networkx as nx


class GraphAnalyzer:
    """
    Forensic analysis routines operating on the transaction relationship graph.
    """

    def compute_metrics(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Computes topological graph metrics.
        """
        if len(G) == 0:
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "address_nodes": 0,
                "tx_nodes": 0,
                "network_ip_nodes": 0,
                "density": 0.0,
                "connected_components": 0,
            }

        addr_count = sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "address")
        tx_count = sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "transaction")
        ip_count = sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "network_ip")

        # Weakly connected components
        wcc_count = nx.number_weakly_connected_components(G)

        # Degree centrality for addresses to highlight hub wallets
        addr_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "address"]
        degrees = dict(G.degree(addr_nodes))
        top_addresses = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "address_nodes": addr_count,
            "tx_nodes": tx_count,
            "network_ip_nodes": ip_count,
            "density": round(nx.density(G), 5),
            "connected_components": wcc_count,
            "top_hub_addresses": top_addresses
        }

    def trace_peeling_chain(self, G: nx.DiGraph, start_address: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        Traces sequential peeling chain transfers originating from a source address.
        """
        steps = []
        curr = start_address
        visited = set()

        for depth in range(max_depth):
            if curr in visited or curr not in G:
                break
            visited.add(curr)

            # Find outgoing tx edges
            out_edges = [v for u, v, d in G.out_edges(curr, data=True) if G.nodes[v].get("node_type") == "transaction"]
            if not out_edges:
                break

            tx_node = out_edges[0]
            tx_data = G.nodes[tx_node]

            # Find receivers of this transaction
            receivers = [v for u, v, d in G.out_edges(tx_node, data=True) if G.nodes[v].get("node_type") == "address"]

            steps.append({
                "step": depth + 1,
                "sender": curr,
                "tx_id": tx_node,
                "amount_btc": tx_data.get("amount_btc", 0.0),
                "anomaly_score": tx_data.get("anomaly_score", 0.0),
                "receivers": receivers
            })

            # In peeling chains, one receiver is a change address that continues the chain
            # We look for a receiver with outgoing edges
            next_step_found = False
            for r in receivers:
                if r not in visited and G.out_degree(r) > 0:
                    curr = r
                    next_step_found = True
                    break

            if not next_step_found:
                break

        return steps

    def find_flow_path(self, G: nx.DiGraph, source: str, target: str) -> Optional[List[str]]:
        """
        Finds the shortest directed path connecting a suspect source to a destination.
        """
        if source not in G or target not in G:
            return None
        try:
            return nx.shortest_path(G, source=source, target=target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
