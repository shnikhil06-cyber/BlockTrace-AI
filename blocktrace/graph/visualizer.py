"""
Interactive Forensic Graph Visualizer for BlockTrace-AI.
Generates dynamic PyVis and Plotly network visualizations for offline investigation.
"""

from typing import Optional, Dict, Any, List
import json
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network


# Dark Cyber Forensic Theme Palette
COLOR_ADDRESS = "#38bdf8"       # Light Sky Blue
COLOR_TX_NORMAL = "#10b981"     # Emerald Green
COLOR_TX_MEDIUM = "#f59e0b"     # Amber
COLOR_TX_HIGH = "#f97316"       # Bright Orange
COLOR_TX_CRITICAL = "#ef4444"   # Neon Crimson
COLOR_NET_IP = "#a855f7"        # Purple
COLOR_ANONYMIZER_IP = "#ec4899" # Magenta / Hot Pink
COLOR_EDGE_FLOW = "rgba(148, 163, 184, 0.45)"
COLOR_EDGE_BROADCAST = "rgba(168, 85, 247, 0.6)"


class GraphVisualizer:
    """
    Renders multi-modal forensic graphs into interactive visual representations.
    """

    def generate_pyvis_html(
        self,
        G: nx.DiGraph,
        filter_tier: Optional[str] = None,
        max_nodes: int = 120,
        height: str = "600px"
    ) -> str:
        """
        Creates an interactive PyVis canvas with physics and dark styling.
        """
        # Filter subgraph if requested
        sub_nodes = set()
        for n, d in G.nodes(data=True):
            if filter_tier and filter_tier != "ALL":
                if d.get("node_type") == "transaction":
                    if d.get("risk_tier") == filter_tier:
                        sub_nodes.add(n)
                        # Include immediate neighbors (addresses/IPs)
                        sub_nodes.update(G.predecessors(n))
                        sub_nodes.update(G.successors(n))
            else:
                sub_nodes.add(n)

        subG = G.subgraph(list(sub_nodes)[:max_nodes]).copy()

        net = Network(
            height=height,
            width="100%",
            directed=True,
            bgcolor="#0b0f19",
            font_color="#f8fafc"
        )

        # Configure physics for smooth dynamic clustering
        net.set_options(json.dumps({
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {"iterations": 150}
            },
            "nodes": {
                "font": {"size": 13, "face": "JetBrains Mono, monospace", "color": "#f1f5f9"}
            },
            "edges": {
                "smooth": {"type": "continuous"},
                "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}}
            },
            "interaction": {
                "hover": True,
                "tooltipDelay": 100,
                "zoomView": True,
                "navigationButtons": True
            }
        }))

        for node_id, data in subG.nodes(data=True):
            ntype = data.get("node_type", "address")
            label = data.get("label", str(node_id)[:10])

            if ntype == "transaction":
                score = data.get("anomaly_score", 0.0)
                tier = data.get("risk_tier", "NORMAL")
                amt = data.get("amount_btc", 0.0)
                pattern = data.get("pattern", "NORMAL")

                if tier == "CRITICAL":
                    color = COLOR_TX_CRITICAL
                    size = 28
                elif tier == "HIGH":
                    color = COLOR_TX_HIGH
                    size = 24
                elif tier == "MEDIUM":
                    color = COLOR_TX_MEDIUM
                    size = 20
                else:
                    color = COLOR_TX_NORMAL
                    size = 16

                title = (
                    f"<b>TRANSACTION</b><br>"
                    f"Hash: {data.get('full_id')}<br>"
                    f"Volume: {amt:.4f} BTC<br>"
                    f"Fee: {data.get('fee_btc', 0):.6f} BTC<br>"
                    f"Risk Score: <b>{score:.1f} ({tier})</b><br>"
                    f"Pattern: {pattern.replace('_', ' ')}"
                )
                net.add_node(
                    node_id,
                    label=label,
                    title=title,
                    color=color,
                    shape="box",
                    size=size
                )

            elif ntype == "network_ip":
                is_tor = data.get("is_tor", False)
                is_bp = data.get("is_bulletproof", False)
                color = COLOR_ANONYMIZER_IP if (is_tor or is_bp) else COLOR_NET_IP

                title = (
                    f"<b>P2P OBSERVER / ORIGIN IP</b><br>"
                    f"IP: {data.get('full_id')}<br>"
                    f"ASN: {data.get('asn')}<br>"
                    f"Country: {data.get('country')}<br>"
                    f"Anonymizer: {'TOR/PROXY' if is_tor else ('BULLETPROOF' if is_bp else 'NO')}"
                )
                net.add_node(
                    node_id,
                    label=label,
                    title=title,
                    color=color,
                    shape="diamond",
                    size=22
                )

            else:  # Address node
                title = f"<b>BITCOIN WALLET</b><br>Address: {data.get('full_id')}"
                net.add_node(
                    node_id,
                    label=label,
                    title=title,
                    color=COLOR_ADDRESS,
                    shape="dot",
                    size=14
                )

        # Add edges
        for u, v, d in subG.edges(data=True):
            etype = d.get("edge_type", "transfer")
            if etype == "broadcast_origin":
                net.add_edge(u, v, color=COLOR_EDGE_BROADCAST, dashes=True, title="P2P Broadcast Origin")
            else:
                amt = d.get("amount_btc", 0.0)
                title = f"{amt:.4f} BTC" if amt > 0 else "Flow"
                net.add_edge(u, v, color=COLOR_EDGE_FLOW, title=title)

        return net.generate_html()

    def generate_plotly_figure(
        self,
        G: nx.DiGraph,
        filter_tier: Optional[str] = None,
        max_nodes: int = 100
    ) -> go.Figure:
        """
        Creates a high-performance offline Plotly 2D interactive network figure.
        """
        sub_nodes = set()
        for n, d in G.nodes(data=True):
            if filter_tier and filter_tier != "ALL":
                if d.get("node_type") == "transaction" and d.get("risk_tier") == filter_tier:
                    sub_nodes.add(n)
                    sub_nodes.update(G.predecessors(n))
                    sub_nodes.update(G.successors(n))
            else:
                sub_nodes.add(n)

        subG = G.subgraph(list(sub_nodes)[:max_nodes]).copy()

        if len(subG) == 0:
            fig = go.Figure()
            fig.update_layout(
                title="No nodes matching the selected filter",
                template="plotly_dark",
                paper_bgcolor="#0b0f19",
                plot_bgcolor="#0b0f19"
            )
            return fig

        pos = nx.spring_layout(subG, seed=42, k=0.45)

        # Edge traces
        edge_x = []
        edge_y = []
        for edge in subG.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=1.2, color="rgba(148, 163, 184, 0.35)"),
            hoverinfo="none",
            mode="lines"
        )

        # Node traces grouped by type
        node_groups = {
            "Critical Tx": {"x": [], "y": [], "text": [], "color": COLOR_TX_CRITICAL, "symbol": "square", "size": 16},
            "High Risk Tx": {"x": [], "y": [], "text": [], "color": COLOR_TX_HIGH, "symbol": "square", "size": 14},
            "Normal Tx": {"x": [], "y": [], "text": [], "color": COLOR_TX_NORMAL, "symbol": "square", "size": 11},
            "Network Node / IP": {"x": [], "y": [], "text": [], "color": COLOR_NET_IP, "symbol": "diamond", "size": 15},
            "Bitcoin Address": {"x": [], "y": [], "text": [], "color": COLOR_ADDRESS, "symbol": "circle", "size": 10},
        }

        for node in subG.nodes():
            x, y = pos[node]
            d = subG.nodes[node]
            ntype = d.get("node_type", "address")

            if ntype == "transaction":
                tier = d.get("risk_tier", "NORMAL")
                score = d.get("anomaly_score", 0.0)
                amt = d.get("amount_btc", 0.0)
                hover = f"TX: {d.get('full_id')[:16]}...<br>Amount: {amt:.4f} BTC<br>Score: {score:.1f} ({tier})<br>Pattern: {d.get('pattern')}"
                if tier == "CRITICAL":
                    group = "Critical Tx"
                elif tier in ("HIGH", "MEDIUM"):
                    group = "High Risk Tx"
                else:
                    group = "Normal Tx"
            elif ntype == "network_ip":
                hover = f"IP: {d.get('full_id')}<br>ASN: {d.get('asn')}<br>Country: {d.get('country')}"
                group = "Network Node / IP"
            else:
                hover = f"Address: {d.get('full_id')}"
                group = "Bitcoin Address"

            node_groups[group]["x"].append(x)
            node_groups[group]["y"].append(y)
            node_groups[group]["text"].append(hover)

        fig = go.Figure(data=[edge_trace])

        for group_name, gdata in node_groups.items():
            if gdata["x"]:
                fig.add_trace(go.Scatter(
                    x=gdata["x"],
                    y=gdata["y"],
                    mode="markers",
                    name=group_name,
                    hoverinfo="text",
                    text=gdata["text"],
                    marker=dict(
                        symbol=gdata["symbol"],
                        size=gdata["size"],
                        color=gdata["color"],
                        line=dict(width=1, color="#ffffff")
                    )
                ))

        fig.update_layout(
            title=dict(
                text="<b>BlockTrace-AI: Forensic Transaction & Network Correlation Graph</b>",
                font=dict(size=16, color="#f8fafc")
            ),
            showlegend=True,
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(15, 23, 42, 0.8)", font=dict(color="#f8fafc")),
            hovermode="closest",
            margin=dict(b=20, l=10, r=10, t=50),
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )

        return fig
