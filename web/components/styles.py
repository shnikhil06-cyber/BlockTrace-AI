"""
Custom CSS and Visual Polish for BlockTrace-AI Cyber Forensics UI.
Provides an elite dark-mode cybersecurity command center visual aesthetic.
"""

def get_custom_css() -> str:
    return """
    <style>
        /* Import Google Fonts: Inter & JetBrains Mono */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            letter-spacing: -0.01em;
        }

        code, pre, .mono-text {
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.88em;
        }

        /* Top Hero Header Bar */
        .hero-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(17, 24, 39, 0.98) 100%);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 14px;
            padding: 20px 28px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px -4px rgba(0, 0, 0, 0.7), 0 0 20px -2px rgba(56, 189, 248, 0.2);
            backdrop-filter: blur(14px);
        }
        .hero-title {
            font-size: 1.65rem;
            font-weight: 800;
            color: #f8fafc;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 0.85rem;
            color: #94a3b8;
            margin-top: 5px;
            font-weight: 400;
        }
        .hero-tags {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }

        /* Cyber Pulse Status Indicator */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 700;
            color: #10b981;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 4px 12px;
            border-radius: 9999px;
            letter-spacing: 0.04em;
        }
        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #10b981;
            box-shadow: 0 0 8px #10b981;
            display: inline-block;
            animation: pulse-glow 2s infinite ease-in-out;
        }
        @keyframes pulse-glow {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        /* Cyber Forensic Metric Cards */
        .metric-card {
            background: linear-gradient(145deg, #0f172a 0%, #111827 100%);
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.4);
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
            height: 100%;
        }
        .metric-card:hover {
            border-color: #0284c7;
            transform: translateY(-2px);
            box-shadow: 0 8px 24px -4px rgba(2, 132, 199, 0.3);
        }
        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #38bdf8, transparent);
            opacity: 0.7;
        }
        .metric-card-critical {
            background: linear-gradient(145deg, rgba(30, 15, 20, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid rgba(239, 68, 68, 0.45);
            box-shadow: 0 4px 18px -2px rgba(239, 68, 68, 0.25);
        }
        .metric-card-critical::before {
            background: linear-gradient(90deg, transparent, #ef4444, transparent);
            opacity: 0.9;
        }
        .metric-card-critical:hover {
            border-color: #ef4444;
            box-shadow: 0 8px 24px -4px rgba(239, 68, 68, 0.4);
        }
        .metric-card-warning {
            background: linear-gradient(145deg, rgba(35, 24, 15, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid rgba(245, 158, 11, 0.45);
            box-shadow: 0 4px 18px -2px rgba(245, 158, 11, 0.25);
        }
        .metric-card-warning::before {
            background: linear-gradient(90deg, transparent, #f59e0b, transparent);
            opacity: 0.9;
        }
        .metric-card-warning:hover {
            border-color: #f59e0b;
            box-shadow: 0 8px 24px -4px rgba(245, 158, 11, 0.4);
        }
        .metric-card-purple {
            background: linear-gradient(145deg, rgba(28, 18, 45, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid rgba(168, 85, 247, 0.45);
            box-shadow: 0 4px 18px -2px rgba(168, 85, 247, 0.25);
        }
        .metric-card-purple::before {
            background: linear-gradient(90deg, transparent, #a855f7, transparent);
            opacity: 0.9;
        }
        .metric-card-purple:hover {
            border-color: #a855f7;
            box-shadow: 0 8px 24px -4px rgba(168, 85, 247, 0.4);
        }
        .metric-card-emerald {
            background: linear-gradient(145deg, rgba(15, 35, 28, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid rgba(16, 185, 129, 0.45);
            box-shadow: 0 4px 18px -2px rgba(16, 185, 129, 0.25);
        }
        .metric-card-emerald::before {
            background: linear-gradient(90deg, transparent, #10b981, transparent);
            opacity: 0.9;
        }
        .metric-label {
            font-size: 0.72rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #94a3b8;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #f8fafc;
            line-height: 1.15;
            font-feature-settings: "tnum" 1;
        }
        .metric-sub {
            font-size: 0.76rem;
            color: #64748b;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Sidebar Tactical Navigation Card Overrides */
        div[data-testid="stRadio"] > div {
            gap: 6px;
        }
        div[data-testid="stRadio"] label {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.5) 100%);
            border: 1px solid rgba(56, 189, 248, 0.12);
            border-radius: 9px;
            padding: 9px 12px;
            margin-bottom: 3px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
        }
        div[data-testid="stRadio"] label:hover {
            background: rgba(56, 189, 248, 0.12);
            border-color: rgba(56, 189, 248, 0.5);
            transform: translateX(3px);
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.18);
        }
        div[data-testid="stRadio"] label[data-checked="true"],
        div[data-testid="stRadio"] label:has(input:checked) {
            background: linear-gradient(135deg, rgba(2, 132, 199, 0.28) 0%, rgba(14, 165, 233, 0.16) 100%) !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.3) !important;
        }
        div[data-testid="stRadio"] label[data-checked="true"] p,
        div[data-testid="stRadio"] label:has(input:checked) p {
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }

        /* Tactical Buttons Styling */
        button[kind="primary"] {
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
            border: 1px solid #38bdf8 !important;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4) !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            transition: all 0.2s ease !important;
            border-radius: 8px !important;
        }
        button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 22px rgba(56, 189, 248, 0.55) !important;
        }
        button[kind="secondary"] {
            background: rgba(15, 23, 42, 0.85) !important;
            border: 1px solid #334155 !important;
            transition: all 0.2s ease !important;
            border-radius: 8px !important;
        }
        button[kind="secondary"]:hover {
            border-color: #38bdf8 !important;
            background: rgba(30, 41, 59, 0.95) !important;
            transform: translateY(-1px) !important;
        }

        /* Styled Tabs with Neon Accents */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease !important;
            border-radius: 6px 6px 0 0 !important;
            padding: 8px 16px !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #38bdf8 !important;
            border-bottom: 2px solid #38bdf8 !important;
            background: rgba(56, 189, 248, 0.08) !important;
        }

        /* Launchpad Empty State Cards */
        .launchpad-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
            margin: 18px 0;
        }
        .launchpad-card {
            background: linear-gradient(135deg, #0b1120 0%, #0f172a 100%);
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.25s ease;
            position: relative;
        }
        .launchpad-card:hover {
            border-color: #38bdf8;
            transform: translateY(-3px);
            box-shadow: 0 8px 24px -4px rgba(56, 189, 248, 0.22);
        }
        .launchpad-step-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #38bdf8;
            font-weight: 800;
            font-size: 0.88rem;
            margin-bottom: 12px;
        }
        .launchpad-card-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #f1f5f9;
            margin-bottom: 6px;
        }
        .launchpad-card-desc {
            font-size: 0.82rem;
            color: #94a3b8;
            line-height: 1.5;
        }

        /* Badges & Tags */
        .badge-critical {
            background-color: rgba(239, 68, 68, 0.16);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.5);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
        }
        .badge-high {
            background-color: rgba(249, 115, 22, 0.16);
            color: #fb923c;
            border: 1px solid rgba(249, 115, 22, 0.5);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
        }
        .badge-medium {
            background-color: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.5);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
        }
        .badge-normal {
            background-color: rgba(16, 185, 129, 0.16);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.5);
            padding: 3px 9px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.72rem;
            letter-spacing: 0.04em;
        }
        .badge-airgap {
            background-color: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
            padding: 4px 11px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        /* Narrative forensic highlight card */
        .forensic-narrative {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.75) 100%);
            border-left: 4px solid #38bdf8;
            border-top: 1px solid #1e293b;
            border-right: 1px solid #1e293b;
            border-bottom: 1px solid #1e293b;
            padding: 16px 20px;
            border-radius: 10px;
            font-size: 0.92rem;
            color: #e2e8f0;
            margin: 12px 0;
            line-height: 1.6;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        }

        /* Alert callout cards in alert feed */
        .alert-card {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 12px;
            transition: all 0.2s ease;
        }
        .alert-card:hover {
            transform: translateX(4px);
            border-color: #38bdf8;
            box-shadow: 0 6px 18px -2px rgba(56, 189, 248, 0.18);
        }

        /* Hop cards for network propagation timeline */
        .hop-card {
            background: #0b1120;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
            transition: border-color 0.2s ease;
        }
        .hop-card:hover {
            border-color: #38bdf8;
        }
        .hop-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }
        .hop-badge-origin {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.5);
        }
        .hop-badge-relay {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
        }

        /* Side-by-side comparison cards */
        .cmp-card-a {
            background: linear-gradient(145deg, #0f172a 0%, #101c38 100%);
            border: 1px solid rgba(56, 189, 248, 0.35);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 14px -2px rgba(56, 189, 248, 0.15);
        }
        .cmp-card-b {
            background: linear-gradient(145deg, #0f172a 0%, #26161a 100%);
            border: 1px solid rgba(249, 115, 22, 0.35);
            border-radius: 12px;
            padding: 16px 20px;
            box-shadow: 0 4px 14px -2px rgba(249, 115, 22, 0.15);
        }

        /* Safety disclaimer box */
        .forensic-disclaimer {
            background: rgba(17, 24, 39, 0.85);
            border: 1px solid #374151;
            padding: 14px 18px;
            border-radius: 10px;
            font-size: 0.82rem;
            color: #94a3b8;
            margin-top: 20px;
            line-height: 1.5;
        }

        /* Streamlit Dataframe and table polish */
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #1e293b;
        }

        /* Sleek scrollbar styling */
        ::-webkit-scrollbar {
            width: 7px;
            height: 7px;
        }
        ::-webkit-scrollbar-track {
            background: #0b0f19;
        }
        ::-webkit-scrollbar-thumb {
            background: #1e293b;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #38bdf8;
        }
    </style>
    """
