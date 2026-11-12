"""
Custom CSS and Visual Polish for BlockTrace-AI Cyber Forensics UI.
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
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(17, 24, 39, 0.95) 100%);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 14px;
            padding: 18px 26px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px -4px rgba(0, 0, 0, 0.6), 0 0 16px -2px rgba(56, 189, 248, 0.15);
            backdrop-filter: blur(12px);
        }
        .hero-title {
            font-size: 1.6rem;
            font-weight: 800;
            color: #f8fafc;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            font-size: 0.84rem;
            color: #94a3b8;
            margin-top: 5px;
            font-weight: 400;
        }
        .hero-tags {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        /* Cyber Pulse Status Indicator */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            color: #10b981;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.4);
            padding: 3px 10px;
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
            box-shadow: 0 8px 24px -4px rgba(2, 132, 199, 0.28);
        }
        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #38bdf8, transparent);
            opacity: 0.5;
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
