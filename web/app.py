"""
BlockTrace-AI: Main Streamlit Forensic Investigation Dashboard.
Offline Bitcoin Forensic Analysis Correlating Blockchain Records with Network Logs
using NetworkX Graph Analysis, Isolation Forest, and SHAP Explainability.
"""

import os
import sys

# Ensure project root is on sys.path for local imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import io
import json
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components

from blocktrace.ingestion import (
    parse_transactions,
    parse_network_logs,
    validate_forensic_data,
)
from blocktrace.correlation import CorrelationEngine, OriginTracer, NetworkClusterer
from blocktrace.ml import (
    extract_forensic_features,
    AnomalyDetector,
    ForensicExplainer,
    FEATURE_LABELS,
)
from blocktrace.graph import ForensicGraphBuilder, GraphAnalyzer, GraphVisualizer
from blocktrace.forensic_case import ForensicCaseManager, ForensicReportExporter
from web.components.styles import get_custom_css
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

# Page Configuration
st.set_page_config(
    page_title="BlockTrace-AI | Bitcoin Forensic Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply Dark Cyber Forensics Styling
st.markdown(get_custom_css(), unsafe_allow_html=True)


# Initialize Session State
def init_session_state():
    if "case_manager" not in st.session_state:
        st.session_state.case_manager = ForensicCaseManager(
            case_id="BT-2026-CASE-081",
            case_title="Bitcoin Laundering & Network Telemetry Investigation",
            investigator="Nikhil Sharma / Tech Titans",
            organization="NST-RU Forensic Research Lab"
        )
    if "df_tx" not in st.session_state:
        st.session_state.df_tx = None
    if "df_net" not in st.session_state:
        st.session_state.df_net = None
    if "dataset_source" not in st.session_state:
        st.session_state.dataset_source = "No dataset loaded"
    if "uploader_nonce" not in st.session_state:
        st.session_state.uploader_nonce = 0
    if "processed" not in st.session_state:
        st.session_state.processed = False


init_session_state()


# Core Processing Pipeline (Cached)
def process_data(df_tx, df_net, contamination=0.08, n_estimators=150):
    correlator = CorrelationEngine()
    df_corr = correlator.correlate(df_tx, df_net)
    summary = correlator.compute_summary(df_corr, df_net)

    X, meta = extract_forensic_features(df_corr)
    detector = AnomalyDetector(contamination=contamination, n_estimators=n_estimators, random_state=42)
    scored_df = detector.fit_predict(X, meta)

    explainer = ForensicExplainer(detector.model, list(X.columns))
    explanations = explainer.explain_dataset(X, scored_df)
    exp_dict = {e["tx_id"]: e for e in explanations}

    builder = ForensicGraphBuilder()
    G = builder.build_graph(scored_df, df_net, max_txs=120)

    analyzer = GraphAnalyzer()
    graph_metrics = analyzer.compute_metrics(G)

    return {
        "df_corr": df_corr,
        "summary": summary,
        "X": X,
        "detector": detector,
        "scored_df": scored_df,
        "explainer": explainer,
        "explanations": explanations,
        "exp_dict": exp_dict,
        "G": G,
        "graph_metrics": graph_metrics,
        "correlator": correlator,
        "analyzer": analyzer,
    }


# Sidebar Navigation & System Telemetry
with st.sidebar:
    st.markdown("### 🛡️ **BlockTrace-AI**")
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <span class="badge-airgap">🔒 OFFLINE AIR-GAPPED [SECURE]</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Team **Tech Titans** • NST-RU Hackathon")

    nav_choice = st.radio(
        "Investigation Module",
        [
            "🛰️ Telemetry & Mission Control",
            "📂 Data Ingestion & Quality",
            "🔗 Correlation Engine",
            "🧠 AI Anomaly & SHAP (XAI)",
            "🕸️ Interactive Graph Forensics",
            "📊 Deep Analytics Dashboard",
            "🌐 Global Threat Intelligence",
            "🔀 Transaction Comparison",
            "📋 Case Dossier & Export",
        ],
        index=0 if st.session_state.df_tx is not None else 1,
    )

    st.markdown("---")
    st.markdown("#### ⚙️ AI Model Parameters")
    contamination_slider = st.slider(
        "Contamination Rate (Anomaly Ratio)",
        min_value=0.01,
        max_value=0.30,
        value=0.08,
        step=0.01,
        help="Expected proportion of outliers in the dataset for Isolation Forest",
    )
    n_trees_slider = st.slider(
        "Isolation Forest Trees",
        min_value=50,
        max_value=300,
        value=150,
        step=25,
    )

    st.markdown("---")
    st.caption("Current Dataset:")
    st.info(f"📄 {st.session_state.dataset_source}")
    if st.session_state.df_tx is not None or st.session_state.df_net is not None:
        if st.button("🗑️ Clear Loaded Dataset", width="stretch"):
            st.session_state.df_tx = None
            st.session_state.df_net = None
            st.session_state.last_tx_file_sig = None
            st.session_state.last_net_file_sig = None
            st.session_state.uploader_nonce += 1
            st.session_state.dataset_source = "No dataset loaded"
            st.rerun()


def render_empty_dataset_notice():
    st.warning("No forensic dataset is currently loaded.")
    st.markdown(
        "Upload a **Bitcoin Transactions** file (`.csv` or `.json`) — and optionally a **P2P Network Observation Logs** file — in **📂 Data Ingestion & Quality** to begin offline analysis."
    )


# Execute Pipeline only when transaction data is loaded
has_data = st.session_state.df_tx is not None and not st.session_state.df_tx.empty
if has_data:
    results = process_data(
        st.session_state.df_tx,
        st.session_state.df_net,
        contamination=contamination_slider,
        n_estimators=n_trees_slider,
    )
    scored_df = results["scored_df"]
    summary = results["summary"]
    exp_dict = results["exp_dict"]
    G = results["G"]
    G_metrics = results["graph_metrics"]
    analyzer = results["analyzer"]
else:
    results = None
    scored_df = pd.DataFrame()
    summary = None
    exp_dict = {}
    G = None
    G_metrics = {}
    analyzer = None


# -----------------------------------------------------------------------------
# TAB 1: TELEMETRY & MISSION CONTROL
# -----------------------------------------------------------------------------
if nav_choice == "🛰️ Telemetry & Mission Control":
    st.title("🛰️ Telemetry & Mission Control")
    st.markdown("Real-time forensic telemetry across correlated Bitcoin transactions and peer-to-peer network observations.")

    if not has_data:
        render_empty_dataset_notice()
        st.stop()

    # KPI Top Bar
    c1, c2, c3, c4, c5 = st.columns(5)
    crit_count = int((scored_df["risk_tier"] == "CRITICAL").sum())
    high_count = int((scored_df["risk_tier"] == "HIGH").sum())
    susp_vol = float(scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])]["amount_btc"].sum())

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Analyzed Transactions</div>
                <div class="metric-value">{summary.total_txs:,}</div>
                <div class="metric-sub">{summary.total_network_logs:,} P2P network logs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Network Correlated</div>
                <div class="metric-value">{summary.correlation_rate_pct:.1f}%</div>
                <div class="metric-sub">{summary.matched_txs} of {summary.total_txs} matched</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Critical Alerts</div>
                <div class="metric-value" style="color:#ef4444;">{crit_count}</div>
                <div class="metric-sub">Score ≥ 80.0 / 100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">High-Risk BTC Volume</div>
                <div class="metric-value" style="color:#f59e0b;">{susp_vol:.2f} ₿</div>
                <div class="metric-sub">Flagged UTXO principal</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Tor / Proxy Relays</div>
                <div class="metric-value" style="color:#ec4899;">{summary.tor_proxy_broadcasts}</div>
                <div class="metric-sub">{summary.bulletproof_broadcasts} bulletproof ASNs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts: Risk Tier Distribution & Anomaly Score Spread
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Risk Tier Breakdown")
        tier_counts = scored_df["risk_tier"].value_counts().reset_index()
        tier_counts.columns = ["Risk Tier", "Count"]
        color_map = {
            "CRITICAL": "#ef4444",
            "HIGH": "#f97316",
            "MEDIUM": "#f59e0b",
            "LOW": "#3b82f6",
            "NORMAL": "#10b981",
        }
        fig_pie = px.pie(
            tier_counts,
            names="Risk Tier",
            values="Count",
            color="Risk Tier",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            font_color="#f8fafc",
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_pie, width="stretch")

    with chart_col2:
        st.subheader("📈 Anomaly Score vs Transaction Volume")
        fig_scatter = px.scatter(
            scored_df,
            x="amount_btc",
            y="anomaly_score",
            color="risk_tier",
            color_discrete_map=color_map,
            hover_data=["tx_id", "earliest_ip", "forensic_pattern", "fee_rate_sat_vb"],
            labels={"amount_btc": "Volume (BTC)", "anomaly_score": "Forensic Risk Score (0-100)"},
        )
        fig_scatter.update_layout(
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            font_color="#f8fafc",
            xaxis=dict(gridcolor="#1e293b"),
            yaxis=dict(gridcolor="#1e293b"),
            margin=dict(t=20, b=20, l=20, r=20),
        )
        st.plotly_chart(fig_scatter, width="stretch")

    # Priority Alert Feed
    st.subheader("🚨 Priority Triage Alert Feed (Top Anomalies)")
    high_risks = scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])].head(6)

    if high_risks.empty:
        st.success("✅ No CRITICAL or HIGH risk alerts detected in this dataset.")
    else:
        for _, alert in high_risks.iterrows():
            tx_id = alert["tx_id"]
            tier = alert["risk_tier"]
            score = alert["anomaly_score"]
            pattern = alert["forensic_pattern"].replace("_", " ")
            vol = alert["amount_btc"]
            ip = alert["earliest_ip"]
            asn = alert["earliest_asn"]
            country = alert["earliest_country"]

            badge_cls = "badge-critical" if tier == "CRITICAL" else "badge-high"

            with st.container():
                st.markdown(
                    f"""
                    <div style="background:#111827; border: 1px solid #374151; border-left: 4px solid {'#ef4444' if tier == 'CRITICAL' else '#f97316'}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div>
                                <span class="{badge_cls}">{tier} ALERT</span>
                                <strong style="color:#f8fafc; margin-left:10px; font-size:1.05rem;">{pattern}</strong>
                                <span style="color:#9ca3af; font-size:0.85rem; margin-left:8px;">(Score: {score:.1f}/100)</span>
                            </div>
                            <div style="color:#38bdf8; font-weight:700; font-size:1.1rem;">{vol:.4f} BTC</div>
                        </div>
                        <div style="font-family:'JetBrains Mono', monospace; font-size:0.8rem; color:#94a3b8; margin-top:6px;">
                            TX: {tx_id} &nbsp;|&nbsp; Origin IP: {ip} ({country}, {asn}) &nbsp;|&nbsp; Rate: {alert['fee_rate_sat_vb']:.1f} sat/vB
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# -----------------------------------------------------------------------------
# TAB 2: DATA INGESTION & QUALITY
# -----------------------------------------------------------------------------
elif nav_choice == "📂 Data Ingestion & Quality":
    st.title("📂 Data Ingestion & Quality Assessment")
    st.markdown("Upload local CSV or JSON files or inspect active dataset schemas in 100% offline air-gapped mode.")

    ing_col1, ing_col2 = st.columns(2)

    with ing_col1:
        st.subheader("📥 Upload Bitcoin Transactions")
        tx_file = st.file_uploader(
            "Choose Transactions File (CSV or JSON)",
            type=["csv", "json"],
            key=f"tx_upload_{st.session_state.uploader_nonce}",
        )
        if tx_file is not None:
            tx_sig = f"{tx_file.name}:{tx_file.size}"
            if st.session_state.get("last_tx_file_sig") != tx_sig:
                try:
                    parsed_tx = parse_transactions(tx_file)
                    st.session_state.df_tx = parsed_tx
                    st.session_state.last_tx_file_sig = tx_sig
                    st.session_state.dataset_source = f"Custom Upload: {tx_file.name} ({len(parsed_tx)} txs)"
                    st.success(f"Successfully ingested {len(parsed_tx)} transaction records!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse transactions file: {str(e)}")

    with ing_col2:
        st.subheader("📥 Upload Network Observation Logs")
        net_file = st.file_uploader(
            "Choose Network Logs File (CSV or JSON)",
            type=["csv", "json"],
            key=f"net_upload_{st.session_state.uploader_nonce}",
        )
        if net_file is not None:
            net_sig = f"{net_file.name}:{net_file.size}"
            if st.session_state.get("last_net_file_sig") != net_sig:
                try:
                    parsed_net = parse_network_logs(net_file)
                    st.session_state.df_net = parsed_net
                    st.session_state.last_net_file_sig = net_sig
                    st.success(f"Successfully ingested {len(parsed_net)} network observation logs!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse network logs file: {str(e)}")

    has_net = st.session_state.df_net is not None and not st.session_state.df_net.empty

    if not has_data:
        st.markdown("---")
        st.info("Upload a **Bitcoin Transactions** CSV or JSON file above to start forensic analysis. Network observation logs are optional.")
        if has_net:
            st.success(f"Loaded **{len(st.session_state.df_net):,}** network observation logs. Upload a matching Bitcoin Transactions file to correlate them.")
            st.subheader("🔍 Ingested Network Logs Preview")
            st.dataframe(
                st.session_state.df_net.head(25),
                width="stretch",
            )
    else:
        st.markdown("---")
        st.subheader("📋 Forensic Data Quality Report")
        val_report = validate_forensic_data(st.session_state.df_tx, st.session_state.df_net)

        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Total Transactions", f"{val_report.tx_count:,}")
        with q2:
            st.metric("Network Logs", f"{val_report.net_log_count:,}")
        with q3:
            st.metric("Network Coverage", f"{val_report.coverage_percentage:.1f}%")
        with q4:
            st.metric("Unique Origin IPs", f"{val_report.unique_ips:,}")

        if val_report.warnings:
            for w in val_report.warnings:
                st.warning(f"⚠️ {w}")

        if has_net:
            tx_ids_set = set(st.session_state.df_tx["tx_id"])
            net_ids_set = set(st.session_state.df_net["tx_id"])
            direct_matches = tx_ids_set.intersection(net_ids_set)

            if len(direct_matches) == 0:
                st.error("⚠️ Network Observation Log transaction IDs do not match the loaded Bitcoin Transactions!")
                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    st.caption("Sample Blockchain Tx IDs:")
                    st.code("\n".join(list(st.session_state.df_tx["tx_id"])[:3]))
                with d_col2:
                    st.caption("Sample Network Log Tx IDs:")
                    st.code("\n".join(list(st.session_state.df_net["tx_id"])[:3]))

                st.markdown(
                    "If your network telemetry logs and blockchain transactions originate from separate monitoring sources, you can auto-link them:"
                )
                if st.button("🔗 Auto-Link Network Logs to Ingested Transactions", width="stretch"):
                    df_net_aligned = st.session_state.df_net.copy()
                    tx_ids_list = list(st.session_state.df_tx["tx_id"])
                    unique_net_txs = list(df_net_aligned["tx_id"].unique())
                    mapping = {}
                    for idx, nid in enumerate(unique_net_txs):
                        mapping[nid] = tx_ids_list[idx % len(tx_ids_list)]
                    df_net_aligned["tx_id"] = df_net_aligned["tx_id"].replace(mapping)
                    st.session_state.df_net = df_net_aligned
                    st.success(f"Aligned {len(df_net_aligned)} network observation logs across {len(tx_ids_list)} transactions!")
                    st.rerun()
            else:
                st.success(
                    f"✅ **{len(direct_matches)} of {len(tx_ids_set)}** transactions matched with network observation logs "
                    f"({len(direct_matches) / max(len(tx_ids_set), 1) * 100.0:.1f}% coverage)."
                )

        st.markdown("---")
        st.subheader("🔍 Ingested Transactions Preview")
        st.dataframe(
            st.session_state.df_tx.head(25),
            width="stretch",
        )

        if has_net:
            st.subheader("🔍 Ingested Network Logs Preview")
            preview_net = st.session_state.df_net.head(25).copy()
            tx_ids_set = set(st.session_state.df_tx["tx_id"])
            preview_net.insert(
                0,
                "correlation_status",
                preview_net["tx_id"].apply(lambda tid: "✅ Matched" if tid in tx_ids_set else "⚠️ Unmatched")
            )
            st.dataframe(
                preview_net,
                width="stretch",
            )
        else:
            st.info("No network observation logs loaded yet.")


# -----------------------------------------------------------------------------
# ALL OTHER TABS REQUIRE LOADED DATA
# -----------------------------------------------------------------------------
elif not has_data:
    st.title(nav_choice)
    render_empty_dataset_notice()


# -----------------------------------------------------------------------------
# TAB 3: CORRELATION ENGINE
# -----------------------------------------------------------------------------
elif nav_choice == "🔗 Correlation Engine":
    st.title("🔗 Cross-Source Correlation Engine")
    st.markdown("Matching Bitcoin blockchain transaction records with peer-to-peer network telemetry to uncover broadcast origins.")

    # Correlation telemetry
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Cross-Correlation Rate", f"{summary.correlation_rate_pct:.1f}%", f"{summary.matched_txs} matched")
    with t2:
        st.metric("Avg Propagation Spread", f"{summary.avg_propagation_spread_ms:.1f} ms")
    with t3:
        st.metric("Avg Confirmation Delay", f"{summary.avg_confirmation_delay_sec:.1f} s")
    with t4:
        st.metric("Geographic Spread", f"{summary.unique_countries} Countries", f"{summary.unique_origin_ips} Origin IPs")

    st.markdown("---")
    st.subheader("🎯 Broadcast Origin Inspector")
    tx_options = scored_df["tx_id"].tolist()
    selected_tx = st.selectbox(
        "Select Transaction Hash to trace P2P origin & propagation hop timeline:",
        tx_options,
        index=0,
    )

    tracer = OriginTracer()
    origin_info = tracer.trace_transaction_origin(selected_tx, st.session_state.df_net)

    if origin_info["status"] == "ORIGIN_IDENTIFIED":
        o1, o2, o3, o4 = st.columns(4)
        with o1:
            st.metric("Earliest Origin IP", origin_info["origin_ip"])
        with o2:
            st.metric("Origin ASN", origin_info["origin_asn"])
        with o3:
            st.metric("Country", origin_info["origin_country"])
        with o4:
            st.metric("Origin Confidence", f"{origin_info['origin_confidence_pct']}%")

        st.caption(f"First Observed UTC: `{origin_info['first_observed_utc']}` • Client: `{origin_info['user_agent']}`")

        st.markdown("#### ⏱️ Network Propagation Hop Timeline")
        df_timeline = pd.DataFrame(origin_info["timeline"])
        st.dataframe(
            df_timeline[["hop_order", "delta_ms", "ip_address", "country", "asn", "event_type", "latency_ms"]],
            width="stretch",
        )
    else:
        st.info("No matching network observations found for this transaction ID.")

    st.markdown("---")
    st.subheader("🌐 Network Clustering by Broadcast Origin IP")
    clusterer = NetworkClusterer()
    ip_clusters = clusterer.cluster_by_origin_ip(results["df_corr"])

    df_clusters = pd.DataFrame(ip_clusters)
    if not df_clusters.empty:
        st.dataframe(
            df_clusters[["cluster_key", "tx_count", "total_amount_btc", "country", "asn", "is_anonymizer", "risk_flag"]],
            width="stretch",
        )


# -----------------------------------------------------------------------------
# TAB 4: AI ANOMALY DETECTION & SHAP (XAI)
# -----------------------------------------------------------------------------
elif nav_choice == "🧠 AI Anomaly & SHAP (XAI)":
    st.title("🧠 AI Anomaly Detection & SHAP Explainability")
    st.markdown("Unsupervised anomaly detection via Isolation Forest with local Shapley feature attributions (Explainable AI).")

    # Filter controls
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        tier_filter = st.selectbox("Filter Risk Tier", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"], index=0)
    with f2:
        pattern_filter = st.selectbox(
            "Filter Pattern Signature",
            ["ALL"] + sorted(list(scored_df["forensic_pattern"].unique())),
            index=0,
        )
    with f3:
        min_score = st.slider("Minimum Forensic Score", min_value=0.0, max_value=100.0, value=30.0, step=5.0)

    # Filter data
    filtered_df = scored_df.copy()
    if tier_filter != "ALL":
        filtered_df = filtered_df[filtered_df["risk_tier"] == tier_filter]
    if pattern_filter != "ALL":
        filtered_df = filtered_df[filtered_df["forensic_pattern"] == pattern_filter]
    filtered_df = filtered_df[filtered_df["anomaly_score"] >= min_score]

    st.subheader(f"Ranked Suspicious Transactions ({len(filtered_df)} matches)")
    st.dataframe(
        filtered_df[[
            "risk_rank", "risk_tier", "anomaly_score", "forensic_pattern",
            "amount_btc", "fee_rate_sat_vb", "earliest_ip", "earliest_asn", "earliest_country"
        ]],
        width="stretch",
    )

    st.markdown("---")
    st.subheader("🔬 Deep-Dive Evidence & SHAP Explanation")

    if not filtered_df.empty:
        inspect_tx = st.selectbox("Select Alert to Inspect Evidence:", filtered_df["tx_id"].tolist(), index=0)
        exp = exp_dict.get(inspect_tx)
        alert_row = scored_df[scored_df["tx_id"] == inspect_tx].iloc[0]

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Anomaly Score", f"{alert_row['anomaly_score']:.1f}/100", alert_row["risk_tier"])
        with d2:
            st.metric("Volume", f"{alert_row['amount_btc']:.4f} BTC")
        with d3:
            st.metric("Fee Density", f"{alert_row['fee_rate_sat_vb']:.1f} sat/vB")
        with d4:
            st.metric("Broadcast Origin IP", alert_row["earliest_ip"])

        # Narrative Explanation Box
        if exp:
            st.markdown(
                f"""
                <div class="forensic-narrative">
                    <strong>Forensic Rationale:</strong><br>
                    {exp['summary_text']}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # SHAP Feature Attribution Plot
            st.markdown("#### 🎯 SHAP Feature Attribution (Local Drivers)")
            top_drivers = exp["top_drivers"]
            df_drivers = pd.DataFrame(top_drivers)

            plot_style = st.radio(
                "SHAP Visualization Format",
                ["Waterfall Plot (Decision Shift)", "Horizontal Impact Ranking"],
                horizontal=True,
                key="shap_plot_style"
            )

            if plot_style == "Waterfall Plot (Decision Shift)":
                fig_wf = results["explainer"].generate_waterfall_figure(exp)
                if fig_wf:
                    st.plotly_chart(fig_wf, width="stretch")
                else:
                    st.info("Waterfall plot unavailable for this item.")
            else:
                fig_shap = px.bar(
                    df_drivers,
                    x="abs_impact",
                    y="label",
                    orientation="h",
                    color="abs_impact",
                    color_continuous_scale="Reds",
                    labels={"abs_impact": "|SHAP Impact| (Anomaly Contribution)", "label": "Feature"},
                    hover_data=["value"],
                )
                fig_shap.update_layout(
                    paper_bgcolor="#0b0f19",
                    plot_bgcolor="#0b0f19",
                    font_color="#f8fafc",
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=20, b=20, l=20, r=20),
                )
                st.plotly_chart(fig_shap, width="stretch")

        # Action: Bookmark to Case Dossier
        st.markdown("#### 📌 Case Dossier Action")
        b_col1, b_col2 = st.columns([3, 1])
        with b_col1:
            investigator_note = st.text_input("Analyst Note for this Evidence:", value="Suspicious flow identified during automated triage.")
        with b_col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔖 Bookmark to Case", width="stretch"):
                st.session_state.case_manager.bookmark_entity(
                    entity_id=inspect_tx,
                    entity_type="transaction",
                    risk_score=alert_row["anomaly_score"],
                    risk_tier=alert_row["risk_tier"],
                    pattern=alert_row["forensic_pattern"],
                    notes=investigator_note,
                )
                st.success(f"Bookmarked {inspect_tx[:12]}... into Case Dossier!")

        st.markdown(
            f"""
            <div class="forensic-disclaimer">
                <strong>Safety & Reliability Protocol:</strong> All anomaly scores are probabilistic risk indicators to assist human investigators in prioritizing forensic review. They do not constitute sole proof of crime.
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# TAB 5: INTERACTIVE GRAPH FORENSICS
# -----------------------------------------------------------------------------
elif nav_choice == "🕸️ Interactive Graph Forensics":
    st.title("🕸️ Interactive Multi-Modal Graph Forensics")
    st.markdown("Directed graph linking Bitcoin Wallets (Addresses), Transactions, and Network P2P Origin IPs.")

    # Graph telemetry
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Graph Nodes", f"{G_metrics['total_nodes']:,}")
    with m2:
        st.metric("Directed Edges", f"{G_metrics['total_edges']:,}")
    with m3:
        st.metric("Bitcoin Addresses", f"{G_metrics['address_nodes']:,}")
    with m4:
        st.metric("P2P Network IPs", f"{G_metrics['network_ip_nodes']:,}")

    st.markdown("---")
    g_ctrl1, g_ctrl2, g_ctrl3 = st.columns([2, 2, 2])
    with g_ctrl1:
        render_engine = st.radio("Visualization Engine", ["Interactive Physics Canvas (PyVis)", "Plotly 2D Graph"], horizontal=True)
    with g_ctrl2:
        graph_tier_filter = st.selectbox("Graph Risk Filter", ["ALL", "CRITICAL", "HIGH", "MEDIUM"], index=0)
    with g_ctrl3:
        max_graph_nodes = st.slider("Max Visible Nodes", min_value=25, max_value=150, value=75, step=25)

    viz = GraphVisualizer()

    if render_engine == "Interactive Physics Canvas (PyVis)":
        st.caption("Drag nodes, zoom, pan, and hover over entities to inspect metadata.")
        pyvis_html = viz.generate_pyvis_html(G, filter_tier=graph_tier_filter, max_nodes=max_graph_nodes, height="620px")
        components.html(pyvis_html, height=640, scrolling=False)
    else:
        plotly_fig = viz.generate_plotly_figure(G, filter_tier=graph_tier_filter, max_nodes=max_graph_nodes)
        st.plotly_chart(plotly_fig, width="stretch")

    st.markdown("---")
    st.subheader("🕵️ Wallets & Path Tracing")
    path_col1, path_col2, path_col3 = st.columns([3, 3, 2])

    addr_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "address"]
    if addr_nodes:
        with path_col1:
            src_addr = st.selectbox("Source Address (Inflow)", addr_nodes, index=0)
        with path_col2:
            tgt_addr = st.selectbox("Target Address (Outflow)", addr_nodes, index=min(1, len(addr_nodes) - 1))
        with path_col3:
            st.markdown("<br>", unsafe_allow_html=True)
            find_path_btn = st.button("🔎 Trace Flow Path", width="stretch")

        if find_path_btn:
            path = analyzer.find_flow_path(G, src_addr, tgt_addr)
            if path:
                st.success(f"Found Directed Flow Path ({len(path)} hops):")
                st.write(" ➔ ".join([f"`{n[:10]}...`" for n in path]))
            else:
                st.info("No direct transfer path found between these two addresses.")


# -----------------------------------------------------------------------------
# TAB 6: CASE DOSSIER & EXPORT
# -----------------------------------------------------------------------------
elif nav_choice == "📋 Case Dossier & Export":
    st.title("📋 Forensic Case Dossier & Evidence Export")
    st.markdown("Compile bookmarked findings, analyst hypotheses, and generate official court-ready audit reports.")

    case = st.session_state.case_manager

    c_meta1, c_meta2, c_meta3 = st.columns(3)
    with c_meta1:
        case.case_id = st.text_input("Case Reference ID", value=case.case_id)
    with c_meta2:
        case.case_title = st.text_input("Investigation Title", value=case.case_title)
    with c_meta3:
        case.investigator = st.text_input("Lead Forensic Investigator", value=case.investigator)

    st.markdown("---")
    st.subheader(f"📌 Bookmarked Evidence Entities ({len(case.bookmarks)})")

    if case.bookmarks:
        bm_records = []
        for entity_id, bm in case.bookmarks.items():
            bm_records.append({
                "Entity ID": entity_id,
                "Type": bm.entity_type,
                "Score": bm.risk_score,
                "Tier": bm.risk_tier,
                "Pattern": bm.pattern,
                "Notes": bm.notes,
                "Timestamp": bm.added_at,
            })
        st.dataframe(pd.DataFrame(bm_records), width="stretch")
    else:
        st.info("No evidence bookmarked yet. Use the '🔖 Bookmark to Case' button in the AI Anomaly tab.")

    st.markdown("---")
    st.subheader("📝 Case Notes Log")
    for n in case.notes:
        st.markdown(f"- {n}")

    new_note = st.text_area("Add Investigator Note:", placeholder="Enter observation, corroborating intelligence, or subpoena ref...")
    if st.button("➕ Add Note to Log"):
        if new_note.strip():
            case.add_note(new_note.strip())
            st.success("Note logged with UTC timestamp.")
            st.rerun()

    st.markdown("---")
    st.subheader("📥 Export Official Forensic Dossier")

    crit_cnt = int((scored_df["risk_tier"] == "CRITICAL").sum())
    high_cnt = int((scored_df["risk_tier"] == "HIGH").sum())
    susp_vol = float(scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])]["amount_btc"].sum())

    stats = {
        "total_txs": summary.total_txs,
        "matched_txs": summary.matched_txs,
        "correlation_rate_pct": summary.correlation_rate_pct,
        "critical_count": crit_cnt,
        "high_count": high_cnt,
        "suspicious_volume_btc": susp_vol,
        "tor_proxy_broadcasts": summary.tor_proxy_broadcasts,
        "bulletproof_broadcasts": summary.bulletproof_broadcasts,
    }

    exporter = ForensicReportExporter()
    explanations_list = results["explanations"]

    html_rep = exporter.generate_html_report(case, stats, scored_df, explanations_list)
    md_rep = exporter.generate_markdown_report(case, stats, scored_df, explanations_list)
    json_rep = exporter.export_json(case, stats, scored_df, explanations_list)

    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        st.download_button(
            label="📄 Download HTML Report (Print / PDF Ready)",
            data=html_rep,
            file_name=f"{case.case_id}_Forensic_Report.html",
            mime="text/html",
            width="stretch",
        )
    with exp_col2:
        st.download_button(
            label="📝 Download Markdown Dossier",
            data=md_rep,
            file_name=f"{case.case_id}_Audit_Report.md",
            mime="text/markdown",
            width="stretch",
        )
    with exp_col3:
        st.download_button(
            label="💾 Download JSON Audit File",
            data=json_rep,
            file_name=f"{case.case_id}_Audit.json",
            mime="application/json",
            width="stretch",
        )


# -----------------------------------------------------------------------------
# TAB 8: DEEP ANALYTICS DASHBOARD
# -----------------------------------------------------------------------------
elif nav_choice == "📊 Deep Analytics Dashboard":
    st.title("📊 Deep Analytics Dashboard")
    st.markdown("Advanced multi-dimensional forensic intelligence visualizations derived from the AI-scored transaction set.")

    # ── Temporal Heatmap ──────────────────────────────────────────────────────
    st.markdown("#### 🕐 Transaction Temporal Activity by Risk Tier")
    fig_heat = build_temporal_heatmap(scored_df)
    if fig_heat:
        st.plotly_chart(fig_heat, width="stretch")
    else:
        st.info("Timestamp data not available for heatmap.")

    st.markdown("---")

    # ── Radar + Fee Distribution (side by side) ───────────────────────────────
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### 🕸️ Behavioral Fingerprint Radar")
        fig_radar = build_radar_comparison(scored_df)
        if fig_radar:
            st.plotly_chart(fig_radar, width="stretch")
        else:
            st.info("Need both CRITICAL/HIGH and NORMAL tier transactions for radar chart.")
    with r2:
        st.markdown("#### 💰 Fee Rate Distribution: Suspicious vs Normal")
        fig_fee = build_fee_distribution_chart(scored_df)
        if fig_fee:
            st.plotly_chart(fig_fee, width="stretch")

    st.markdown("---")

    # ── Propagation Scatter ───────────────────────────────────────────────────
    st.markdown("#### 📡 P2P Propagation Speed vs Forensic Risk Score")
    fig_prop = build_propagation_scatter(scored_df)
    if fig_prop:
        st.plotly_chart(fig_prop, width="stretch")
    else:
        st.info("No network-correlated transactions available.")

    st.markdown("---")

    # ── Sunburst ──────────────────────────────────────────────────────────────
    st.markdown("#### 🌸 Attack Pattern Signature Distribution (Sunburst)")
    fig_sun = build_pattern_sunburst(scored_df)
    if fig_sun:
        st.plotly_chart(fig_sun, width="stretch")

    st.markdown("---")

    # ── Sankey Flow ───────────────────────────────────────────────────────────
    st.markdown("#### 🔀 Bitcoin Flow Sankey: Sender → Transaction → Receiver")
    max_sankey = st.slider("Max transactions in Sankey", min_value=5, max_value=30, value=12, step=1)
    fig_sankey = build_sankey_flow(scored_df, max_txs=max_sankey)
    if fig_sankey:
        st.plotly_chart(fig_sankey, width="stretch")
    else:
        st.info("No address data available for Sankey flow.")


# -----------------------------------------------------------------------------
# TAB 9: GLOBAL THREAT INTELLIGENCE
# -----------------------------------------------------------------------------
elif nav_choice == "🌐 Global Threat Intelligence":
    st.title("🌐 Global Threat Intelligence")
    st.markdown("Geographic and behavioral profiling of Bitcoin broadcast origins and high-risk wallet addresses.")

    # ── Geo Map ───────────────────────────────────────────────────────────────
    st.markdown("#### 🗺️ P2P Broadcast Origin World Map")
    df_net = st.session_state.df_net
    fig_geo = build_geo_broadcast_map(scored_df, df_net)
    if fig_geo:
        st.plotly_chart(fig_geo, width="stretch")
    else:
        st.info("No country-level broadcast data found. Upload P2P network observation logs to correlate broadcast origins.")

    st.markdown("---")

    # ── Wallet Risk Profiles ──────────────────────────────────────────────────
    st.markdown("#### 🏦 Wallet / Address Risk Profiles")
    wallet_df = build_wallet_risk_profiles(scored_df)

    if not wallet_df.empty:
        g1, g2 = st.columns([2, 1])
        with g1:
            max_wallets = min(200, len(wallet_df))
            min_wallets = min(5, max_wallets)
            if max_wallets > min_wallets:
                top_n = st.slider("Show top N wallets by max risk score", min_value=min_wallets, max_value=max_wallets, value=min(30, max_wallets))
            else:
                top_n = max_wallets
        with g2:
            tier_filter = st.multiselect(
                "Filter by dominant tier",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NORMAL"],
                default=["CRITICAL", "HIGH"],
            )

        display_df = wallet_df.copy()
        if tier_filter:
            display_df = display_df[display_df["dominant_tier"].isin(tier_filter)]
        display_df = display_df.head(top_n)

        # Color-code by dominant tier
        tier_color_map_st = {
            "CRITICAL": "background-color: rgba(239,68,68,0.15)",
            "HIGH": "background-color: rgba(249,115,22,0.15)",
            "MEDIUM": "background-color: rgba(245,158,11,0.10)",
            "LOW": "background-color: rgba(59,130,246,0.10)",
            "NORMAL": "background-color: rgba(16,185,129,0.08)",
        }

        def _style_tier_row(row):
            style = tier_color_map_st.get(row["dominant_tier"], "")
            return [style] * len(row)

        styled = display_df.style.apply(_style_tier_row, axis=1).format({
            "max_risk_score": "{:.1f}",
            "mean_risk_score": "{:.1f}",
            "total_btc": "{:.4f}",
        })

        st.dataframe(styled, width="stretch")

        # CSV Download
        csv_bytes = display_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Wallet Profiles as CSV",
            data=csv_bytes,
            file_name="blocktrace_wallet_risk_profiles.csv",
            mime="text/csv",
        )
    else:
        st.info("No address-level data found in the current scored dataset.")

    st.markdown("---")

    # ── ASN Cluster Table ──────────────────────────────────────────────────────
    st.markdown("#### 🌐 ASN / Network Cluster Analysis")
    clusterer = NetworkClusterer()
    # cluster_by_asn() needs the correlated+scored DataFrame (has 'network_correlated', 'earliest_asn')
    clusters = clusterer.cluster_by_asn(scored_df) if not scored_df.empty else []
    if clusters:
        asn_rows = []
        for c in clusters:
            asn_rows.append({
                "ASN": c["cluster_key"],
                "Tx Count": c["tx_count"],
                "Unique IPs": c["unique_ips"],
                "Total BTC": f"{c['total_amount_btc']:.4f}",
                "Countries": ", ".join(c["countries"][:4]),
            })
        asn_df = pd.DataFrame(asn_rows)
        st.dataframe(asn_df, width="stretch")
    else:
        st.info("No ASN clustering data available.")


# -----------------------------------------------------------------------------
# TAB 10: TRANSACTION COMPARISON
# -----------------------------------------------------------------------------
elif nav_choice == "🔀 Transaction Comparison":
    st.title("🔀 Transaction Feature Comparison")
    st.markdown("Select any two transactions to perform a side-by-side forensic feature comparison.")

    all_tx_ids = scored_df["tx_id"].tolist()

    if len(all_tx_ids) < 2:
        st.warning("Need at least 2 transactions in the dataset to compare.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            default_a = all_tx_ids[0]
            tx_id_a = st.selectbox("🔵 Transaction A", all_tx_ids, index=0, key="cmp_tx_a")
        with col_b:
            default_b = all_tx_ids[1] if all_tx_ids[1] != tx_id_a else all_tx_ids[2] if len(all_tx_ids) > 2 else all_tx_ids[0]
            tx_b_options = [t for t in all_tx_ids if t != tx_id_a]
            tx_id_b = st.selectbox("🟠 Transaction B", tx_b_options, index=0, key="cmp_tx_b")

        row_a = scored_df[scored_df["tx_id"] == tx_id_a].iloc[0]
        row_b = scored_df[scored_df["tx_id"] == tx_id_b].iloc[0]

        # Metric summaries
        m1, m2, m3, m4 = st.columns(4)
        tier_badge = {
            "CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "NORMAL": "🟢"
        }
        with m1:
            st.metric("TX A — Risk Score", f"{row_a['anomaly_score']:.1f}", delta=None)
            st.caption(f"{tier_badge.get(row_a['risk_tier'], '')} {row_a['risk_tier']}")
        with m2:
            st.metric("TX A — Pattern", row_a["forensic_pattern"].replace("_", " "))
        with m3:
            st.metric("TX B — Risk Score", f"{row_b['anomaly_score']:.1f}", delta=None)
            st.caption(f"{tier_badge.get(row_b['risk_tier'], '')} {row_b['risk_tier']}")
        with m4:
            st.metric("TX B — Pattern", row_b["forensic_pattern"].replace("_", " "))

        st.markdown("---")

        # Feature comparison chart
        fig_cmp = build_comparison_chart(tx_id_a, tx_id_b, scored_df, results["X"], exp_dict)
        if fig_cmp:
            st.plotly_chart(fig_cmp, width="stretch")

        st.markdown("---")

        # Side-by-side narrative explanations
        n1, n2 = st.columns(2)
        exp_a = exp_dict.get(tx_id_a)
        exp_b = exp_dict.get(tx_id_b)

        with n1:
            st.markdown(f"##### 🔵 TX A Forensic Narrative")
            if exp_a:
                st.markdown(
                    f"""<div class="forensic-narrative">{exp_a['summary_text']}</div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("Top SHAP Feature Drivers (TX A)"):
                    for driver in exp_a["top_drivers"][:6]:
                        feat = driver["label"]
                        shap_val = driver["shap_impact"]
                        bar_pct = int(min(abs(shap_val) * 100, 100))
                        color = "#ef4444" if shap_val > 0 else "#10b981"
                        st.markdown(
                            f"<div style='margin-bottom:4px'><span style='color:#94a3b8;font-size:12px'>{feat}</span>"
                            f"<div style='background:{color};width:{bar_pct}%;height:6px;border-radius:3px;margin-top:2px'></div></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info("No SHAP explanation available for TX A.")

        with n2:
            st.markdown(f"##### 🟠 TX B Forensic Narrative")
            if exp_b:
                st.markdown(
                    f"""<div class="forensic-narrative">{exp_b['summary_text']}</div>""",
                    unsafe_allow_html=True,
                )
                with st.expander("Top SHAP Feature Drivers (TX B)"):
                    for driver in exp_b["top_drivers"][:6]:
                        feat = driver["label"]
                        shap_val = driver["shap_impact"]
                        bar_pct = int(min(abs(shap_val) * 100, 100))
                        color = "#ef4444" if shap_val > 0 else "#10b981"
                        st.markdown(
                            f"<div style='margin-bottom:4px'><span style='color:#94a3b8;font-size:12px'>{feat}</span>"
                            f"<div style='background:{color};width:{bar_pct}%;height:6px;border-radius:3px;margin-top:2px'></div></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info("No SHAP explanation available for TX B.")

        # Additional raw metrics side-by-side
        st.markdown("---")
        st.markdown("##### 📐 Raw Feature Comparison")
        raw_cols = ["amount_btc", "fee_rate_sat_vb", "input_count", "output_count",
                    "observed_node_count", "propagation_spread_ms", "is_tor_proxy_origin",
                    "is_bulletproof_origin", "earliest_ip", "earliest_country"]
        raw_rows = []
        for col in raw_cols:
            va = row_a.get(col, "N/A")
            vb = row_b.get(col, "N/A")
            raw_rows.append({"Feature": col.replace("_", " ").title(), "TX A": str(va), "TX B": str(vb)})
        st.dataframe(pd.DataFrame(raw_rows), width="stretch")

