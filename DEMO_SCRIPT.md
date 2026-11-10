# 🎤 BlockTrace-AI: Official Pitch & Demo Script
**Team: Tech Titans** • Track B (coNSTruct 2.0 Ideathon)  
**Members:** Ramit Layek, Nikhil Sharma, Mayank Sharma

---

## 🎯 3-Minute Live Presentation Structure

### 1. The Hook & The Problem (45 Seconds)
- **Speaker**: Ramit / Nikhil
- **Slide Reference**: Slide 2 & 3
- **Script**:
  > *"Judges, when law enforcement or cybersecurity analysts investigate a ransomware extortion or exchange hack, they face a massive blind spot: **Blockchain data and P2P network telemetry are completely siloed.**
  > On-chain explorers show wallets and amounts, but they tell you nothing about the physical network: Which peer broadcasted it? Was it sent through a Tor exit node in Amsterdam or a bulletproof host in Eastern Europe?
  > Right now, investigators waste days manually correlating timestamps across fragmented spreadsheets. And worst of all, they cannot upload sensitive evidence to cloud APIs due to legal chain-of-custody rules.
  > **Enter BlockTrace-AI: the first 100% offline-first forensic workbench that correlates on-chain records with P2P network telemetry using Explainable AI.**"*

---

### 2. Live Demo Walkthrough (90 Seconds)
- **Speaker**: Nikhil
- **Action**: Switch to browser at `http://localhost:8501` and navigate to **"🎯 Live Pitch Demo Walkthrough"** tab (or direct tabs).

#### Step 1: 1-Click Scenario Load (Telemetry Tab)
- Click **"🌀 Peeling Chain Laundering"** or **"💥 Ransomware Fan-Out"**.
- Point out:
  - Total Analyzed: 110+ Txs, 600+ network observations.
  - Correlation Match Rate: **100% offline cross-correlation**.
  - Air-gapped badge: Runs locally on Linux/macOS with **zero cloud dependencies**.

#### Step 2: The Network Origin Revelation (Correlation Engine Tab)
- Select the top suspicious transaction:
  > *"Look at this transaction: on-chain it looks like a regular transfer. But our cross-correlation engine matches it with network logs in milliseconds:
  > • First seen at IP `185.220.101.20` via Tor Exit Node (AS200052, Netherlands).
  > • First broadcast confidence: **95%** with sub-50ms synchronized propagation spread."*

#### Step 3: Explainable AI with SHAP (AI Anomaly Tab)
- Click on the alert:
  > *"Why did our AI flag this? We don't use black-box models. We trained an Isolation Forest on joint blockchain-network features, and we use **SHAP (Shapley Additive exPlanations)**.
  > Look at this Waterfall Chart: It shows judges and courts exactly which features pushed the risk score to 99/100:
  > 1. Abnormal fee density (+0.31 SHAP)
  > 2. Tor exit node broadcast origin (+0.26 SHAP)
  > 3. 1-to-28 rapid fan-out (+0.22 SHAP)
  > Human investigators stay in complete control."*

#### Step 4: Interactive Graph & Legal Dossier (Graph & Export Tabs)
- Show the **PyVis Interactive Physics Graph**:
  > *"Our multi-modal graph links Bitcoin Wallets (blue), Transactions (red/orange for risk), and P2P Origin IPs (purple). We can trace 8 consecutive peeling hops visually."*
- Click **"Download HTML Forensic Report"**:
  > *"With one click, the investigator exports a court-admissible, tamper-evident Forensic Dossier complete with cryptographic timestamps and executive telemetry."*

---

### 3. The 3-Week Build Plan & Closing (45 Seconds)
- **Speaker**: Mayank
- **Slide Reference**: Slide 6
- **Script**:
  > *"In our pitch deck, we laid out an ambitious 3-week build plan:
  > • Week 1: Offline Ingestion & Correlation Engine — **COMPLETED**
  > • Week 2: Isolation Forest & SHAP Explainability — **COMPLETED**
  > • Week 3: Interactive Dashboard & Court Reporting — **COMPLETED**
  > We have fully delivered the entire pipeline, backed by automated unit test suites and CLI batch automation.
  > BlockTrace-AI equips investigators to solve crypto crime faster, with explainable evidence and zero cloud leaks. Thank you!"*

---

## ❓ Anticipated Judge Q&A Cheatsheet

### Q1: *"Why Isolation Forest instead of a simple rule like 'amount > 10 BTC'?"*
> **Answer**: *"Laundering techniques like peeling chains and mixer tumblers intentionally break transactions into amounts below traditional detection thresholds (e.g. 0.3 BTC). Isolation Forest evaluates multivariate interactions simultaneously—combining fee density, fan-out degree, Tor relay presence, and network latency spread."*

### Q2: *"Why is SHAP necessary?"*
> **Answer**: *"In legal prosecutions and courtrooms, a machine learning score alone is inadmissible as hearsay or a black box. SHAP mathematically computes the exact marginal contribution of each physical feature to the anomaly score, providing evidence-based justification for forensic subpoenas."*

### Q3: *"Can this run on real Bitcoin nodes?"*
> **Answer**: *"Yes! Our CSV and JSON parsers accept standard exports from Bitcoin Core debug logs (`debug.log`), P2P mempool dumps, and standard blockchain explorers. It runs completely air-gapped without needing live internet access."*
