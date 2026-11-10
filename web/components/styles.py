"""
Custom CSS and Styling for BlockTrace-AI Dark Cyber Forensics UI.
"""

def get_custom_css() -> str:
    return """
    <style>
        /* Global typography & background */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        code, pre, .mono-text {
            font-family: 'JetBrains Mono', monospace !important;
        }

        /* Metric cards */
        .metric-card {
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 16px 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            transition: border-color 0.2s ease, transform 0.2s ease;
        }
        .metric-card:hover {
            border-color: #38bdf8;
            transform: translateY(-2px);
        }
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #9ca3af;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 800;
            color: #f9fafb;
            line-height: 1.1;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: #6b7280;
            margin-top: 6px;
        }

        /* Badges */
        .badge-critical {
            background-color: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid #ef4444;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .badge-high {
            background-color: rgba(249, 115, 22, 0.2);
            color: #fb923c;
            border: 1px solid #f97316;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .badge-medium {
            background-color: rgba(245, 158, 11, 0.2);
            color: #fbbf24;
            border: 1px solid #f59e0b;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .badge-normal {
            background-color: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid #10b981;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.75rem;
        }
        .badge-airgap {
            background-color: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid #0284c7;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }

        /* Narrative forensic highlight box */
        .forensic-narrative {
            background: #0f172a;
            border-left: 4px solid #38bdf8;
            padding: 14px 18px;
            border-radius: 6px;
            font-size: 0.92rem;
            color: #e2e8f0;
            margin: 12px 0;
            line-height: 1.5;
        }

        /* Disclaimer */
        .forensic-disclaimer {
            background: rgba(30, 27, 75, 0.6);
            border: 1px solid #4338ca;
            padding: 12px 16px;
            border-radius: 6px;
            font-size: 0.8rem;
            color: #c7d2fe;
            margin-top: 15px;
        }
    </style>
    """

