"""
Command Line Interface (CLI) for BlockTrace-AI.
Enables automated headless batch analysis, scenario generation, and report building offline.
"""

import argparse
import sys
import os
import json
import pandas as pd

from blocktrace.ingestion import parse_transactions, parse_network_logs, validate_forensic_data, save_synthetic_data_to_disk
from blocktrace.correlation import CorrelationEngine, OriginTracer, NetworkClusterer
from blocktrace.ml import extract_forensic_features, AnomalyDetector, ForensicExplainer
from blocktrace.graph import ForensicGraphBuilder, GraphAnalyzer, GraphVisualizer
from blocktrace.forensic_case import ForensicCaseManager, ForensicReportExporter


def run_pipeline(
    tx_path: str,
    net_path: str = None,
    out_html: str = "forensic_report.html",
    out_json: str = None,
    contamination: float = 0.08
):
    print("=================================================================")
    print("🔍 BlockTrace-AI: Offline Bitcoin Forensic Analysis Pipeline")
    print("=================================================================")

    # 1. Ingestion
    print(f"\n[1/5] Ingesting transaction data from: {tx_path}")
    df_tx = parse_transactions(tx_path)
    print(f"      Loaded {len(df_tx)} transaction records.")

    df_net = None
    if net_path and os.path.exists(net_path):
        print(f"[1/5] Ingesting network logs from: {net_path}")
        df_net = parse_network_logs(net_path)
        print(f"      Loaded {len(df_net)} network observation logs.")

    # Validation
    val_report = validate_forensic_data(df_tx, df_net)
    print(f"      Data Validation: {'VALID' if val_report.is_valid else 'ERRORS DETECTED'}")
    if val_report.warnings:
        for w in val_report.warnings[:3]:
            print(f"      [Notice] {w}")

    # 2. Correlation
    print("\n[2/5] Correlating on-chain transactions with P2P network telemetry...")
    correlator = CorrelationEngine()
    df_correlated = correlator.correlate(df_tx, df_net)
    summary = correlator.compute_summary(df_correlated, df_net)
    print(f"      Correlation Rate: {summary.correlation_rate_pct:.1f}% ({summary.matched_txs}/{summary.total_txs})")
    print(f"      Identified {summary.unique_origin_ips} unique broadcast origin IPs across {summary.unique_countries} countries.")

    # 3. ML Anomaly Detection & SHAP
    print("\n[3/5] Extracting forensic features & fitting Isolation Forest (XAI)...")
    X, meta = extract_forensic_features(df_correlated)
    detector = AnomalyDetector(contamination=contamination)
    scored_df = detector.fit_predict(X, meta)

    critical_cnt = int((scored_df["risk_tier"] == "CRITICAL").sum())
    high_cnt = int((scored_df["risk_tier"] == "HIGH").sum())
    suspicious_btc = float(scored_df[scored_df["risk_tier"].isin(["CRITICAL", "HIGH"])]["amount_btc"].sum())

    print(f"      Flagged Alerts: {critical_cnt} CRITICAL, {high_cnt} HIGH risk.")
    print(f"      Total Suspicious Volume: {suspicious_btc:.4f} BTC")

    # SHAP Explanations
    explainer = ForensicExplainer(detector.model, list(X.columns))
    explanations = explainer.explain_dataset(X, scored_df)
    print("      Computed explainable SHAP attributions for flagged transactions.")

    # 4. Graph Construction
    print("\n[4/5] Building multi-modal forensic relationship graph...")
    builder = ForensicGraphBuilder()
    G = builder.build_graph(scored_df, df_net, max_txs=100)
    analyzer = GraphAnalyzer()
    graph_metrics = analyzer.compute_metrics(G)
    print(f"      Graph constructed: {graph_metrics['total_nodes']} nodes, {graph_metrics['total_edges']} directed edges.")

    # 5. Reporting
    print("\n[5/5] Generating Forensic Investigation Dossier...")
    case = ForensicCaseManager(
        case_id="BT-BATCH-AUTO",
        case_title="Automated Offline Forensic Investigation",
        investigator="Automated BlockTrace Pipeline",
        organization="Tech Titans Forensics"
    )

    stats = {
        "total_txs": summary.total_txs,
        "matched_txs": summary.matched_txs,
        "correlation_rate_pct": summary.correlation_rate_pct,
        "critical_count": critical_cnt,
        "high_count": high_cnt,
        "suspicious_volume_btc": suspicious_btc,
        "tor_proxy_broadcasts": summary.tor_proxy_broadcasts,
        "bulletproof_broadcasts": summary.bulletproof_broadcasts,
    }

    exporter = ForensicReportExporter()
    html_report = exporter.generate_html_report(case, stats, scored_df, explanations)

    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"      [✓] Forensic HTML Report saved to: {out_html}")

    if out_json:
        json_report = exporter.export_json(case, stats, scored_df, explanations)
        with open(out_json, "w", encoding="utf-8") as f:
            f.write(json_report)
        print(f"      [✓] Structured JSON Audit File saved to: {out_json}")

    print("\n=================================================================")
    print("🎯 Execution Completed Successfully. Top 3 Highest Risk Alerts:")
    print("=================================================================")
    for _, row in scored_df.head(3).iterrows():
        tx_id = row['tx_id']
        print(f"  • [{row['risk_tier']}] Score: {row['anomaly_score']:.1f}/100 | Tx: {tx_id[:16]}...")
        print(f"    Volume: {row['amount_btc']:.4f} BTC | Sat/vB: {row['fee_rate_sat_vb']:.1f} | Origin IP: {row['earliest_ip']} ({row['earliest_asn']})")
        print(f"    Pattern: {row['forensic_pattern']}")
    print("=================================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="BlockTrace-AI: Offline Bitcoin forensic analysis correlating blockchain with network logs."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Run subcommand
    run_parser = subparsers.add_parser("run", help="Run forensic correlation and anomaly detection pipeline")
    run_parser.add_argument("--txs", required=True, help="Path to Bitcoin transactions CSV/JSON")
    run_parser.add_argument("--net", required=False, help="Path to network observations CSV/JSON")
    run_parser.add_argument("--out", default="forensic_report.html", help="Path to save HTML report")
    run_parser.add_argument("--json", default=None, help="Path to save JSON audit export")
    run_parser.add_argument("--contamination", type=float, default=0.08, help="Expected anomaly ratio")

    # Generate subcommand
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic forensic scenarios and sample datasets")
    gen_parser.add_argument("--out-dir", default="data", help="Output directory for generated files")

    # Demo subcommand
    demo_parser = subparsers.add_parser("demo", help="Run quick demo on built-in synthetic datasets")

    args = parser.parse_args()

    if args.command == "generate":
        print(f"Generating synthetic forensic datasets into '{args.out_dir}'...")
        save_synthetic_data_to_disk(args.out_dir)
        print("Done!")
    elif args.command == "demo":
        save_synthetic_data_to_disk("data")
        run_pipeline(
            tx_path="data/sample/bitcoin_transactions.csv",
            net_path="data/sample/network_observations.csv",
            out_html="demo_forensic_report.html",
            out_json="demo_forensic_report.json"
        )
    elif args.command == "run":
        run_pipeline(
            tx_path=args.txs,
            net_path=args.net,
            out_html=args.out,
            out_json=args.json,
            contamination=args.contamination
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
