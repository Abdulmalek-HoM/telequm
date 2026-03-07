"""
TELEQUM v2.1 — Digital Twin Dashboard
=======================================

Main Streamlit entry point.

Run with:
    streamlit run dashboard/app.py

Or from project root:
    python -m streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Ensure project root is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ─── Page Config ─────────────────────────────────────────────────

st.set_page_config(
    page_title="TELEQUM v2.1 — Quantum-Telecom Digital Twin",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────

st.markdown("""
<style>
    /* TELEQUM Dark Theme Overrides */
    .stApp {
        background-color: #0F172A;
    }
    .stSidebar {
        background-color: #1E293B;
    }
    h1, h2, h3 {
        color: #E2E8F0 !important;
    }
    .stMetric label {
        color: #94A3B8 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #00D4AA !important;
        font-weight: 700;
    }

    /* Accent bar */
    .telequm-bar {
        background: linear-gradient(90deg, #2D5BFF, #6C3AED, #00D4AA);
        height: 3px;
        border-radius: 2px;
        margin-bottom: 1rem;
    }

    /* Sidebar branding */
    .sidebar-brand {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid #334155;
        margin-bottom: 1rem;
    }
    .sidebar-brand h2 {
        background: linear-gradient(135deg, #2D5BFF, #00D4AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        margin: 0;
    }
    .sidebar-brand p {
        color: #94A3B8;
        font-size: 0.85rem;
        margin: 0.25rem 0 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>🔬 TELEQUM</h2>
        <p>v2.1 — Quantum-Telecom Digital Twin</p>
    </div>
    """, unsafe_allow_html=True)

    tab_selection = st.radio(
        "Navigate",
        ["🎓 Education Hub", "🧪 Use-Case Lab",
         "🖥️ Hardware Hub", "🌐 Digital Twin"],
        key="nav_tab",
    )

    st.divider()
    st.caption("© 2026 Abdulmalek Baitulmal")
    st.caption("TELEQUM — Applied Quantum for Telecom")

# ─── Gradient Bar ────────────────────────────────────────────────

st.markdown('<div class="telequm-bar"></div>', unsafe_allow_html=True)

# ─── Tab Routing ─────────────────────────────────────────────────

if tab_selection == "🎓 Education Hub":
    from dashboard.components.education_hub import render
    render()
elif tab_selection == "🧪 Use-Case Lab":
    from dashboard.components.use_case_lab import render
    render()
elif tab_selection == "🖥️ Hardware Hub":
    from dashboard.components.hardware_hub import render
    render()
elif tab_selection == "🌐 Digital Twin":
    from dashboard.components.digital_twin import render
    render()
