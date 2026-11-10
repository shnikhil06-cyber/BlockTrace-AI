"""
Advanced Analytics and Feature Extensions for BlockTrace-AI.
Provides wallet risk profiling, temporal analysis, geo-mapping, and comparative tools.
"""

from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ─── 1. WALLET / ADDRESS RISK PROFILER ─────────────────────────────────────

def build_wallet_risk_profiles(scored_df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds per-address risk profile by aggregating risk of all transactions
    where the address appeared as a sender or receiver.
    Returns a DataFrame with one row per unique address.
    """
    records = []

    for _, row in scored_df.iterrows():
        tx_id = row["tx_id"]
        score = float(row.get("anomaly_score", 0.0))
        tier = str(row.get("risk_tier", "NORMAL"))
        pattern = str(row.get("forensic_pattern", "BENIGN_PROFILE"))
        amt = float(row.get("amount_btc", 0.0))
        fee_rate = float(row.get("fee_rate_sat_vb", 0.0))

        senders = row.get("sender_addresses", [])
        receivers = row.get("receiver_addresses", [])

        for addr in senders:
            if addr:
                records.append({
                    "address": str(addr),
                    "role": "sender",
                    "tx_id": tx_id,
                    "anomaly_score": score,
                    "risk_tier": tier,
                    "pattern": pattern,
                    "amount_btc": amt,
                    "fee_rate_sat_vb": fee_rate,
                })
        for addr in receivers:
            if addr:
                records.append({
                    "address": str(addr),
                    "role": "receiver",
                    "tx_id": tx_id,
                    "anomaly_score": score,
                    "risk_tier": tier,
                    "pattern": pattern,
                    "amount_btc": amt,
                    "fee_rate_sat_vb": fee_rate,
                })

    if not records:
        return pd.DataFrame()

    df_records = pd.DataFrame(records)

    profile = df_records.groupby("address").agg(
        tx_count=("tx_id", "nunique"),
        total_btc=("amount_btc", "sum"),
        max_risk_score=("anomaly_score", "max"),
        mean_risk_score=("anomaly_score", "mean"),
        sender_count=("role", lambda x: (x == "sender").sum()),
        receiver_count=("role", lambda x: (x == "receiver").sum()),
    ).reset_index()

    # Dominant risk tier per address
    tier_map = df_records.groupby("address")["risk_tier"].agg(lambda x: x.value_counts().idxmax()).reset_index()
    tier_map.columns = ["address", "dominant_tier"]

    pattern_map = df_records.groupby("address")["pattern"].agg(lambda x: x.value_counts().idxmax()).reset_index()
    pattern_map.columns = ["address", "dominant_pattern"]

    profile = profile.merge(tier_map, on="address").merge(pattern_map, on="address")

    profile["risk_rank"] = profile["max_risk_score"].rank(ascending=False, method="min").astype(int)
    profile = profile.sort_values("max_risk_score", ascending=False).reset_index(drop=True)

    return profile


# ─── 2. TEMPORAL ACTIVITY HEATMAP ──────────────────────────────────────────

def build_temporal_heatmap(scored_df: pd.DataFrame) -> go.Figure:
    """
    Interactive Plotly heatmap of transaction activity segmented by hour-of-day × risk tier.
    """
    df = scored_df.copy()
    if "timestamp" not in df.columns:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"])

    df["hour_of_day"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date.astype(str)
    df["date_hour"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:00")

    # Pivot: rows = risk tier (ordered), cols = hour of day, values = count
    tier_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"]
    hourly = (
        df.groupby(["risk_tier", "hour_of_day"])
        .size()
        .reset_index(name="count")
    )

    pivot = hourly.pivot(index="risk_tier", columns="hour_of_day", values="count").fillna(0)
    pivot = pivot.reindex(tier_order, fill_value=0)
    # Ensure all 24 hours present
    for h in range(24):
        if h not in pivot.columns:
            pivot[h] = 0
    pivot = pivot[sorted(pivot.columns)]

    colorscales = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#f59e0b",
        "LOW": "#3b82f6",
        "NORMAL": "#10b981",
    }

    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in sorted(pivot.columns)],
        y=pivot.index.tolist(),
        colorscale=[
            [0, "#0b0f19"],
            [0.25, "#1e3a5f"],
            [0.6, "#f59e0b"],
            [1.0, "#ef4444"]
        ],
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>Hour: %{x}<br>Transaction Count: <b>%{z}</b><extra></extra>",
        colorbar=dict(
            title=dict(text="Tx Count", font=dict(color="#f8fafc")),
            tickfont=dict(color="#f8fafc"),
        )
    ))

    fig.update_layout(
        title=dict(text="<b>Transaction Temporal Activity Heatmap by Risk Tier × Hour of Day (UTC)</b>", font=dict(size=14, color="#f8fafc")),
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font_color="#f8fafc",
        xaxis=dict(title="Hour of Day (UTC)", gridcolor="#1e293b"),
        yaxis=dict(title="Risk Tier", gridcolor="#1e293b"),
        margin=dict(t=50, b=40, l=100, r=20),
        height=280,
    )

    return fig


# ─── 3. MULTI-AXIS RADAR CHART: SUSPICIOUS vs NORMAL ───────────────────────

def build_radar_comparison(scored_df: pd.DataFrame) -> go.Figure:
    """
    Radar chart comparing feature averages of CRITICAL/HIGH vs NORMAL transactions.
    Shows the multi-dimensional behavioral gap.
    """
    features = {
        "Fee Density\n(sat/vB)": "fee_rate_sat_vb",
        "Output\nFan-out": "output_count",
        "Volume\n(BTC)": "amount_btc",
        "P2P Observers": "observed_node_count",
        "Propagation\nSpread (ms)": "propagation_spread_ms",
        "Confirmation\nDelay (s)": "confirmation_delay_sec",
    }

    suspicious = scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])]
    normal = scored_df[scored_df["risk_tier"] == "NORMAL"]

    if suspicious.empty or normal.empty:
        return None

    def normalize_means(df_group, cols):
        means = {}
        for label, col in cols.items():
            if col in df_group.columns:
                means[label] = float(df_group[col].mean())
            else:
                means[label] = 0.0
        vals = list(means.values())
        max_val = max(vals) if max(vals) > 0 else 1.0
        return {k: v / max_val for k, v in means.items()}

    all_means = {}
    for label, col in features.items():
        if col in scored_df.columns:
            susp_v = float(suspicious[col].mean()) if not suspicious.empty else 0.0
            norm_v = float(normal[col].mean()) if not normal.empty else 0.0
            all_means[label] = (susp_v, norm_v)

    labels = list(all_means.keys())
    susp_vals = [all_means[l][0] for l in labels]
    norm_vals = [all_means[l][1] for l in labels]

    # Normalize across both groups
    combined_max = [max(susp_vals[i], norm_vals[i], 0.001) for i in range(len(labels))]
    susp_norm = [susp_vals[i] / combined_max[i] for i in range(len(labels))]
    norm_norm = [norm_vals[i] / combined_max[i] for i in range(len(labels))]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=susp_norm + [susp_norm[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="CRITICAL / HIGH Risk",
        line=dict(color="#ef4444", width=2.5),
        fillcolor="rgba(239, 68, 68, 0.2)",
        hovertemplate="<b>%{theta}</b><br>Norm. Value: %{r:.2f}<extra></extra>",
    ))

    fig.add_trace(go.Scatterpolar(
        r=norm_norm + [norm_norm[0]],
        theta=labels + [labels[0]],
        fill="toself",
        name="NORMAL (Baseline)",
        line=dict(color="#10b981", width=2),
        fillcolor="rgba(16, 185, 129, 0.15)",
        hovertemplate="<b>%{theta}</b><br>Norm. Value: %{r:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text="<b>Behavioral Fingerprint Radar: Suspicious vs Baseline</b>", font=dict(size=14, color="#f8fafc")),
        polar=dict(
            bgcolor="#111827",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#374151", linecolor="#374151", tickfont=dict(color="#9ca3af")),
            angularaxis=dict(tickfont=dict(color="#f8fafc"), gridcolor="#374151", linecolor="#374151"),
        ),
        paper_bgcolor="#0b0f19",
        font_color="#f8fafc",
        legend=dict(bgcolor="rgba(15,23,42,0.8)", font=dict(color="#f8fafc")),
        margin=dict(t=50, b=20, l=60, r=60),
        height=380,
    )

    return fig


# ─── 4. WORLD GEOMAP OF BROADCAST ORIGIN IPS ───────────────────────────────

COUNTRY_CODES = {
    "US": ("United States", 37.09, -95.71),
    "DE": ("Germany", 51.17, 10.45),
    "NL": ("Netherlands", 52.13, 5.29),
    "SG": ("Singapore", 1.35, 103.82),
    "JP": ("Japan", 36.20, 138.25),
    "CH": ("Switzerland", 46.82, 8.23),
    "IS": ("Iceland", 64.96, -19.02),
    "SE": ("Sweden", 60.13, 18.64),
    "CA": ("Canada", 56.13, -106.35),
    "GB": ("United Kingdom", 55.38, -3.44),
    "RU": ("Russia", 61.52, 105.32),
    "RO": ("Romania", 45.94, 24.97),
    "CN": ("China", 35.86, 104.19),
    "FR": ("France", 46.23, 2.21),
    "AU": ("Australia", -25.27, 133.78),
    "UA": ("Ukraine", 48.38, 31.17),
    "IR": ("Iran", 32.43, 53.69),
    "UNKNOWN": ("Unknown", 0.0, 0.0),
}


def build_geo_broadcast_map(scored_df: pd.DataFrame, df_net: Optional[pd.DataFrame] = None) -> go.Figure:
    """
    Interactive Plotly globe showing broadcast origin IPs by country, sized by transaction count
    and colored by average risk score.
    """
    if "earliest_country" not in scored_df.columns:
        return None

    agg = (
        scored_df[scored_df["network_correlated"] == True]
        .groupby("earliest_country")
        .agg(
            tx_count=("tx_id", "count"),
            avg_score=("anomaly_score", "mean"),
            max_score=("anomaly_score", "max"),
            total_btc=("amount_btc", "sum"),
            has_critical=("risk_tier", lambda x: (x == "CRITICAL").any()),
        )
        .reset_index()
    )

    # Attach coordinates
    lats, lons, names = [], [], []
    for _, row in agg.iterrows():
        cc = str(row["earliest_country"]).upper()
        info = COUNTRY_CODES.get(cc, COUNTRY_CODES["UNKNOWN"])
        names.append(info[0])
        lats.append(info[1])
        lons.append(info[2])

    agg["country_name"] = names
    agg["lat"] = lats
    agg["lon"] = lons

    agg = agg[(agg["lat"] != 0.0) | (agg["lon"] != 0.0)]

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        lat=agg["lat"],
        lon=agg["lon"],
        mode="markers",
        marker=dict(
            size=np.sqrt(agg["tx_count"]) * 7 + 8,
            color=agg["avg_score"],
            colorscale=[
                [0.0, "#10b981"],
                [0.5, "#f59e0b"],
                [0.8, "#f97316"],
                [1.0, "#ef4444"]
            ],
            cmin=0,
            cmax=100,
            colorbar=dict(
                title=dict(text="Avg Risk Score", font=dict(color="#f8fafc")),
                tickfont=dict(color="#f8fafc"),
            ),
            line=dict(color="#ffffff", width=1),
            opacity=0.85,
            symbol=[
                "star" if row["has_critical"] else "circle"
                for _, row in agg.iterrows()
            ],
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Transactions: %{customdata[0]}<br>"
            "Avg Risk Score: %{customdata[1]:.1f}<br>"
            "Total Volume: %{customdata[2]:.4f} BTC<br>"
            "⭐ = Has CRITICAL alerts<extra></extra>"
        ),
        text=agg["country_name"],
        customdata=list(zip(agg["tx_count"], agg["avg_score"], agg["total_btc"])),
        name="Broadcast Origins",
    ))

    # Add lines from each origin to center to show global spread effect
    fig.update_geos(
        projection_type="natural earth",
        showocean=True,
        oceancolor="#0b0f19",
        showland=True,
        landcolor="#1e293b",
        showcoastlines=True,
        coastlinecolor="#374151",
        showcountries=True,
        countrycolor="#374151",
        showframe=False,
        bgcolor="#0b0f19",
    )

    fig.update_layout(
        title=dict(text="<b>🌐 Global P2P Broadcast Origin Map (Circle Size = Tx Volume, ⭐ = Critical Alert)</b>", font=dict(size=14, color="#f8fafc")),
        paper_bgcolor="#0b0f19",
        font_color="#f8fafc",
        geo=dict(bgcolor="#0b0f19"),
        margin=dict(t=50, b=10, l=10, r=10),
        height=420,
    )

    return fig


# ─── 5. SIDE-BY-SIDE TRANSACTION COMPARISON ────────────────────────────────

def build_comparison_chart(
    tx_id_a: str,
    tx_id_b: str,
    scored_df: pd.DataFrame,
    X: pd.DataFrame,
    exp_dict: Dict[str, Any],
) -> go.Figure:
    """
    Side-by-side feature comparison Plotly grouped bar chart for two transactions.
    """
    features_to_compare = [
        "amount_btc", "fee_rate_sat_vb", "fee_to_amount_ratio",
        "input_count", "output_count", "io_ratio",
        "observed_node_count", "propagation_spread_ms",
        "mean_latency_ms", "burst_velocity",
        "is_tor_proxy", "is_bulletproof",
    ]

    labels_map = {
        "amount_btc": "Volume (BTC)",
        "fee_rate_sat_vb": "Fee Density (sat/vB)",
        "fee_to_amount_ratio": "Fee/Amount Ratio",
        "input_count": "Input Count",
        "output_count": "Output Count",
        "io_ratio": "IO Ratio",
        "observed_node_count": "P2P Observers",
        "propagation_spread_ms": "Propagation Spread (ms)",
        "mean_latency_ms": "Mean Latency (ms)",
        "burst_velocity": "Burst Velocity (tx/s)",
        "is_tor_proxy": "Tor Origin (0/1)",
        "is_bulletproof": "Bulletproof ASN (0/1)",
    }

    idx_a = scored_df[scored_df["tx_id"] == tx_id_a].index
    idx_b = scored_df[scored_df["tx_id"] == tx_id_b].index

    if idx_a.empty or idx_b.empty:
        return None

    row_a = X.loc[idx_a[0]] if idx_a[0] in X.index else None
    row_b = X.loc[idx_b[0]] if idx_b[0] in X.index else None

    if row_a is None or row_b is None:
        return None

    labels = []
    vals_a = []
    vals_b = []

    for feat in features_to_compare:
        if feat in row_a.index and feat in row_b.index:
            labels.append(labels_map.get(feat, feat))
            # Normalize both by their combined max for visual comparison
            va = float(row_a[feat])
            vb = float(row_b[feat])
            combined_max = max(abs(va), abs(vb), 0.001)
            vals_a.append(va / combined_max)
            vals_b.append(vb / combined_max)

    score_a = float(scored_df[scored_df["tx_id"] == tx_id_a]["anomaly_score"].iloc[0])
    score_b = float(scored_df[scored_df["tx_id"] == tx_id_b]["anomaly_score"].iloc[0])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name=f"TX A ({tx_id_a[:10]}...) — Score: {score_a:.0f}",
        x=labels,
        y=vals_a,
        marker_color="#38bdf8",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Norm. Value: %{y:.3f}<extra>TX A</extra>",
    ))

    fig.add_trace(go.Bar(
        name=f"TX B ({tx_id_b[:10]}...) — Score: {score_b:.0f}",
        x=labels,
        y=vals_b,
        marker_color="#f97316",
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Norm. Value: %{y:.3f}<extra>TX B</extra>",
    ))

    fig.update_layout(
        title=dict(text="<b>Feature-Level Side-by-Side Transaction Comparison (Normalized)</b>", font=dict(size=14, color="#f8fafc")),
        barmode="group",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font_color="#f8fafc",
        xaxis=dict(tickangle=-30, gridcolor="#1e293b"),
        yaxis=dict(title="Normalized Feature Value", gridcolor="#1e293b"),
        legend=dict(bgcolor="rgba(15,23,42,0.8)", font=dict(color="#f8fafc")),
        margin=dict(t=50, b=80, l=50, r=20),
        height=380,
    )

    return fig


# ─── 6. FEE RATE DISTRIBUTION: SUSPICIOUS vs NORMAL ─────────────────────────

def build_fee_distribution_chart(scored_df: pd.DataFrame) -> go.Figure:
    """
    Overlapping KDE-style histogram comparing fee rates of suspicious vs normal transactions.
    """
    suspicious = scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH", "MEDIUM"])]["fee_rate_sat_vb"]
    normal = scored_df[scored_df["risk_tier"] == "NORMAL"]["fee_rate_sat_vb"]

    fig = go.Figure()

    if not suspicious.empty:
        fig.add_trace(go.Histogram(
            x=suspicious,
            name="Suspicious (CRITICAL/HIGH/MEDIUM)",
            marker_color="#ef4444",
            opacity=0.65,
            nbinsx=30,
            histnorm="probability density",
            hovertemplate="Fee Rate: %{x:.1f} sat/vB<br>Density: %{y:.4f}<extra>SUSPICIOUS</extra>",
        ))

    if not normal.empty:
        fig.add_trace(go.Histogram(
            x=normal,
            name="Normal (Baseline)",
            marker_color="#10b981",
            opacity=0.60,
            nbinsx=30,
            histnorm="probability density",
            hovertemplate="Fee Rate: %{x:.1f} sat/vB<br>Density: %{y:.4f}<extra>NORMAL</extra>",
        ))

    fig.update_layout(
        title=dict(text="<b>Fee Rate Distribution: Suspicious vs Normal Transactions</b>", font=dict(size=14, color="#f8fafc")),
        barmode="overlay",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font_color="#f8fafc",
        xaxis=dict(title="Fee Rate (sat/vB)", gridcolor="#1e293b"),
        yaxis=dict(title="Probability Density", gridcolor="#1e293b"),
        legend=dict(bgcolor="rgba(15,23,42,0.8)", font=dict(color="#f8fafc")),
        margin=dict(t=50, b=40, l=60, r=20),
        height=320,
    )

    return fig


# ─── 7. PATTERN SIGNATURE OVERVIEW SUNBURST ─────────────────────────────────

def build_pattern_sunburst(scored_df: pd.DataFrame) -> go.Figure:
    """
    Multi-level Plotly sunburst: Risk Tier → Attack Pattern → Count
    """
    agg = (
        scored_df.groupby(["risk_tier", "forensic_pattern"])
        .agg(count=("tx_id", "count"), total_btc=("amount_btc", "sum"))
        .reset_index()
    )

    tier_colors = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#f59e0b",
        "LOW": "#3b82f6",
        "NORMAL": "#10b981",
    }

    ids = []
    labels = []
    parents = []
    values = []
    colors = []

    # Level 1: Risk Tiers
    for tier in agg["risk_tier"].unique():
        total = int(agg[agg["risk_tier"] == tier]["count"].sum())
        ids.append(tier)
        labels.append(f"{tier} ({total})")
        parents.append("")
        values.append(total)
        colors.append(tier_colors.get(tier, "#6b7280"))

    # Level 2: Patterns under each tier
    for _, row in agg.iterrows():
        pid = f"{row['risk_tier']}::{row['forensic_pattern']}"
        ids.append(pid)
        labels.append(f"{row['forensic_pattern'].replace('_', ' ')} ({int(row['count'])})")
        parents.append(row["risk_tier"])
        values.append(int(row["count"]))
        colors.append(tier_colors.get(row["risk_tier"], "#6b7280"))

    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(colors=colors, line=dict(color="#0b0f19", width=1.5)),
        hovertemplate="<b>%{label}</b><br>Tx Count: <b>%{value}</b><extra></extra>",
        branchvalues="total",
        textfont=dict(color="#f8fafc"),
        insidetextorientation="radial",
    ))

    fig.update_layout(
        title=dict(text="<b>Attack Pattern Signature Distribution (Risk Tier → Pattern)</b>", font=dict(size=14, color="#f8fafc")),
        paper_bgcolor="#0b0f19",
        font_color="#f8fafc",
        margin=dict(t=50, b=10, l=10, r=10),
        height=380,
    )

    return fig


# ─── 8. PROPAGATION SPEED ANOMALY SCATTER ───────────────────────────────────

def build_propagation_scatter(scored_df: pd.DataFrame) -> go.Figure:
    """
    Scatter: Propagation Spread (ms) vs Anomaly Score, colored by risk tier, sized by BTC volume.
    """
    df = scored_df[scored_df["network_correlated"] == True].copy()
    if df.empty:
        return None

    tier_colors = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#f59e0b",
        "LOW": "#3b82f6",
        "NORMAL": "#10b981",
    }

    df["color"] = df["risk_tier"].map(tier_colors).fillna("#6b7280")
    df["size"] = (np.log1p(df["amount_btc"]) * 8 + 8).clip(upper=35)
    df["label"] = df.apply(
        lambda r: f"TX: {str(r['tx_id'])[:12]}...<br>Score: {r['anomaly_score']:.1f}<br>Pattern: {r['forensic_pattern']}<br>Origin: {r['earliest_ip']} ({r['earliest_country']})",
        axis=1
    )

    fig = go.Figure()

    for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"]:
        t_df = df[df["risk_tier"] == tier]
        if t_df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=t_df["propagation_spread_ms"],
            y=t_df["anomaly_score"],
            mode="markers",
            name=tier,
            marker=dict(
                size=t_df["size"],
                color=tier_colors[tier],
                line=dict(width=1, color="#ffffff"),
                opacity=0.80,
            ),
            hovertemplate="%{text}<extra></extra>",
            text=t_df["label"],
        ))

    fig.update_layout(
        title=dict(text="<b>P2P Propagation Speed vs Forensic Risk Score (Bubble Size = BTC Volume)</b>", font=dict(size=14, color="#f8fafc")),
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font_color="#f8fafc",
        xaxis=dict(title="Propagation Spread (ms)", gridcolor="#1e293b"),
        yaxis=dict(title="Forensic Risk Score (0–100)", gridcolor="#1e293b"),
        legend=dict(bgcolor="rgba(15,23,42,0.8)", font=dict(color="#f8fafc")),
        margin=dict(t=50, b=40, l=60, r=20),
        height=380,
    )

    return fig


# ─── 9. CHAIN-LINK FLOW SANKEY DIAGRAM ──────────────────────────────────────

def build_sankey_flow(scored_df: pd.DataFrame, max_txs: int = 20) -> go.Figure:
    """
    Plotly Sankey diagram showing BTC flows from sender → transaction → receiver.
    Limited to top anomalous transactions for readability.
    """
    top_txs = scored_df.head(max_txs)

    node_labels = []
    node_colors = []
    source_idxs = []
    target_idxs = []
    link_values = []
    link_labels = []

    tier_color_map = {
        "CRITICAL": "rgba(239,68,68,0.9)",
        "HIGH": "rgba(249,115,22,0.9)",
        "MEDIUM": "rgba(245,158,11,0.9)",
        "LOW": "rgba(59,130,246,0.9)",
        "NORMAL": "rgba(16,185,129,0.9)",
    }

    node_index = {}

    def get_or_add(label: str, color: str) -> int:
        if label not in node_index:
            node_index[label] = len(node_labels)
            node_labels.append(label)
            node_colors.append(color)
        return node_index[label]

    for _, row in top_txs.iterrows():
        tx_id = str(row["tx_id"])
        tx_label = f"TX:{tx_id[:8]}..."
        tier = str(row.get("risk_tier", "NORMAL"))
        amt = float(row.get("amount_btc", 0.01))
        tx_color = tier_color_map.get(tier, "rgba(107,114,128,0.8)")

        tx_idx = get_or_add(tx_label, tx_color)

        senders = row.get("sender_addresses", [])
        receivers = row.get("receiver_addresses", [])

        # Sender → TX
        if isinstance(senders, list):
            for addr in senders[:2]:  # Limit for readability
                addr = str(addr)
                s_label = f"{addr[:8]}..."
                s_idx = get_or_add(s_label, "rgba(56,189,248,0.7)")
                split_amt = round(amt / max(len(senders), 1), 4)
                source_idxs.append(s_idx)
                target_idxs.append(tx_idx)
                link_values.append(max(split_amt, 0.0001))
                link_labels.append(f"{split_amt:.4f} BTC")

        # TX → Receiver
        if isinstance(receivers, list):
            for addr in receivers[:2]:
                addr = str(addr)
                r_label = f"{addr[:8]}..."
                r_idx = get_or_add(r_label, "rgba(168,85,247,0.7)")
                split_amt = round(amt / max(len(receivers), 1), 4)
                source_idxs.append(tx_idx)
                target_idxs.append(r_idx)
                link_values.append(max(split_amt, 0.0001))
                link_labels.append(f"{split_amt:.4f} BTC")

    if not source_idxs:
        return None

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=18,
            thickness=18,
            line=dict(color="#0b0f19", width=0.5),
            label=node_labels,
            color=node_colors,
            hovertemplate="<b>%{label}</b><extra></extra>",
        ),
        link=dict(
            source=source_idxs,
            target=target_idxs,
            value=link_values,
            label=link_labels,
            color="rgba(148, 163, 184, 0.3)",
            hovertemplate="<b>%{label}</b><br>%{source.label} → %{target.label}<extra></extra>",
        ),
    ))

    fig.update_layout(
        title=dict(text=f"<b>Bitcoin Flow Sankey: Sender → Transaction → Receiver (Top {max_txs} Alerts)</b>", font=dict(size=14, color="#f8fafc")),
        paper_bgcolor="#0b0f19",
        font_color="#f8fafc",
        margin=dict(t=55, b=20, l=20, r=20),
        height=450,
    )

    return fig
