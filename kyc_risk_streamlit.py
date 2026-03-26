"""
KYC Risk Investigator — Streamlit App
Autonomous KYC Risk Investigation Portal for AML / compliance teams.

Agentic workflow:
  1. Traditional ML model scores the alert (sanctions proximity, PEP, geo risk…)
  2. Agent collects evidence (documents, news, transaction patterns)
  3. Generative AI produces a plain-English risk narrative
  4. Human investigator reviews evidence and records their decision
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

from kyc_sample_data import KYC_CASES

load_dotenv()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KYC Risk Investigator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f0f2f6 !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}
[data-testid="stSidebar"] {
    background: #1a2540 !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label { color: #94a3b8 !important; }

/* ── Header banner ── */
.kyc-header {
    background: linear-gradient(135deg, #1a2540 0%, #0f3460 100%);
    border-radius: 12px; padding: 20px 28px; margin-bottom: 18px;
    color: white;
}
.kyc-header h1 { margin: 0 0 4px 0; font-size: 1.4rem; font-weight: 700; color: white; }
.kyc-header p  { margin: 0; font-size: 0.85rem; color: #94a3b8; }

/* ── Risk score badge ── */
.risk-badge {
    display: inline-block; padding: 4px 14px; border-radius: 20px;
    font-weight: 700; font-size: 0.85rem; letter-spacing: 0.5px;
}
.risk-high    { background: #fef2f2; color: #991b1b; border: 1.5px solid #fca5a5; }
.risk-medium  { background: #fffbeb; color: #92400e; border: 1.5px solid #fcd34d; }
.risk-low     { background: #f0fdf4; color: #166534; border: 1.5px solid #86efac; }

/* ── Cards ── */
.card {
    background: white; border-radius: 10px; padding: 16px 20px;
    border: 1px solid #e2e8f0; margin-bottom: 12px;
}
.card-title {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; color: #64748b; margin-bottom: 10px;
}

/* ── Risk factor rows ── */
.factor-row {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 0; border-bottom: 1px solid #f1f5f9;
}
.factor-row:last-child { border-bottom: none; }
.factor-name { flex: 1; font-size: 0.87rem; font-weight: 600; color: #1e293b; }
.factor-detail { flex: 2; font-size: 0.82rem; color: #64748b; }

/* ── Score bar ── */
.score-bar-wrap { width: 80px; height: 6px; background: #e2e8f0; border-radius: 3px; }
.score-bar { height: 6px; border-radius: 3px; }

/* ── News item ── */
.news-item {
    background: #f8fafc; border-left: 3px solid #60a5fa;
    padding: 10px 14px; border-radius: 0 8px 8px 0; margin-bottom: 10px;
}
.news-item.high  { border-color: #ef4444; }
.news-item.medium { border-color: #f59e0b; }
.news-source { font-size: 0.75rem; color: #94a3b8; margin-bottom: 3px; }
.news-headline { font-size: 0.88rem; font-weight: 600; color: #1e293b; margin-bottom: 4px; }
.news-snippet { font-size: 0.82rem; color: #475569; }

/* ── AI narrative box ── */
.ai-narrative {
    background: #f0f9ff; border: 1px solid #bae6fd;
    border-radius: 10px; padding: 16px 20px;
}

/* ── Decision panel ── */
.decision-header {
    font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.5px; color: #64748b; margin-bottom: 8px;
}

/* ── Doc row ── */
.doc-row {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px;
}
.doc-type { font-size: 0.82rem; font-weight: 700; color: #1e293b; }
.doc-flag { font-size: 0.78rem; color: #b45309; background: #fffbeb;
            border: 1px solid #fcd34d; border-radius: 4px; padding: 2px 8px;
            display: inline-block; margin-top: 4px; }

/* ── Streamlit component tweaks ── */
.stTabs [data-baseweb="tab"] { font-size: 0.85rem; font-weight: 600; }
div[data-testid="metric-container"] { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────
TIER_CLASS = {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}
DECISION_OPTIONS = [
    "CLEAR — Proceed with standard monitoring",
    "ENHANCED DUE DILIGENCE — Request additional documentation",
    "ESCALATE — Refer to Level 2 compliance review",
    "REJECT / FILE SAR — Suspicious Activity Report required",
]
DECISION_KEYS = ["CLEAR", "ENHANCED_DD", "ESCALATE", "REJECT_SAR"]


def score_bar_html(score: int, tier: str) -> str:
    colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
    color = colors.get(tier, "#94a3b8")
    return (
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar" style="width:{score}%;background:{color}"></div>'
        f'</div>'
    )


def risk_badge_html(tier: str, label: str = None) -> str:
    cls = TIER_CLASS.get(tier, "risk-low")
    text = label or tier
    return f'<span class="risk-badge {cls}">{text}</span>'


def export_decision(case: dict, decision: str, comment: str, reviewer: str) -> dict:
    return {
        "schema_version": "1.0",
        "review_id": str(uuid.uuid4())[:8].upper(),
        "case_id": case["case_id"],
        "client": case["profile"].get("entity_name") or case["profile"].get("entity_name"),
        "alert_type": case["alert_type"],
        "risk_score": case["risk_score"],
        "ml_recommendation": case["ml_scores"]["model_recommendation"],
        "investigator": reviewer,
        "decision": decision,
        "comment": comment,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": case["ml_scores"]["model_version"],
    }


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar() -> dict:
    st.sidebar.markdown("## 🔍 KYC Investigator")
    st.sidebar.markdown("---")

    case_labels = [f"{c['case_id']} — {c['profile'].get('entity_name','')}" for c in KYC_CASES]
    idx = st.sidebar.selectbox("Active Case", range(len(case_labels)), format_func=lambda i: case_labels[i])
    case = KYC_CASES[idx]

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Case Summary**")
    st.sidebar.write(f"Type: `{case['client_type']}`")
    st.sidebar.write(f"Alert: {case['alert_type']}")
    st.sidebar.write(f"Date: {case['alert_date']}")

    tier = case["risk_tier"]
    score = case["risk_score"]
    color = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}.get(tier, "#64748b")
    st.sidebar.markdown(
        f"<div style='margin-top:8px;padding:12px;background:#0d2137;border-radius:8px;"
        f"border:1px solid #1e3a5f;text-align:center'>"
        f"<div style='font-size:0.7rem;color:#94a3b8;margin-bottom:4px'>COMPOSITE RISK SCORE</div>"
        f"<div style='font-size:2rem;font-weight:800;color:{color}'>{score}</div>"
        f"<div style='font-size:0.75rem;font-weight:700;color:{color}'>{tier} RISK</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**ML Model**")
    ml = case["ml_scores"]
    st.sidebar.write(f"Recommendation: **{ml['model_recommendation']}**")
    st.sidebar.write(f"Confidence: {ml['model_confidence']:.0%}")
    st.sidebar.write(f"Model: `{ml['model_version']}`")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='font-size:0.75rem;color:#475569'>Powered by traditional risk scoring + "
        "generative AI narrative</div>",
        unsafe_allow_html=True,
    )
    return case


# ── Profile tab ────────────────────────────────────────────────────────────────
def render_profile(case: dict) -> None:
    profile = case["profile"]
    st.markdown('<div class="card"><div class="card-title">Client Profile</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    items = list(profile.items())
    half = (len(items) + 1) // 2
    for i, (k, v) in enumerate(items):
        label = k.replace("_", " ").title()
        (cols[0] if i < half else cols[1]).metric(label, str(v))
    st.markdown("</div>", unsafe_allow_html=True)


# ── Risk factors tab ───────────────────────────────────────────────────────────
def render_risk_factors(case: dict) -> None:
    ml = case["ml_scores"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Composite Score", f"{ml['composite_risk_score']}/100")
    c2.metric("Sanctions Match P", f"{ml['sanctions_match_probability']:.0%}")
    c3.metric("PEP Connection P", f"{ml['pep_connection_probability']:.0%}")
    c4.metric("AML Flag P", f"{ml['aml_flag_probability']:.0%}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card"><div class="card-title">Risk Factor Breakdown</div>', unsafe_allow_html=True)

    header_html = (
        "<div style='display:flex;gap:10px;padding:4px 0;border-bottom:2px solid #e2e8f0;margin-bottom:6px'>"
        "<span style='flex:1;font-size:0.75rem;font-weight:700;color:#64748b'>FACTOR</span>"
        "<span style='width:80px;font-size:0.75rem;font-weight:700;color:#64748b'>SCORE</span>"
        "<span style='width:60px;font-size:0.75rem;font-weight:700;color:#64748b'>TIER</span>"
        "<span style='flex:2;font-size:0.75rem;font-weight:700;color:#64748b'>DETAIL</span>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    for rf in case["risk_factors"]:
        row = (
            f'<div class="factor-row">'
            f'<span class="factor-name">{rf["factor"]}</span>'
            f'<span style="width:80px">{score_bar_html(rf["score"], rf["tier"])}'
            f'<span style="font-size:0.75rem;color:#64748b">{rf["score"]}</span></span>'
            f'<span style="width:60px">{risk_badge_html(rf["tier"])}</span>'
            f'<span class="factor-detail">{rf["detail"]}</span>'
            f'</div>'
        )
        st.markdown(row, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Documents tab ──────────────────────────────────────────────────────────────
def render_documents(case: dict) -> None:
    st.markdown("**Extracted Document Analysis**")
    for doc in case["documents"]:
        doc_type = doc.get("doc_type", "Document")
        status = doc.get("status", "Unknown")
        icon = "✅" if status == "Extracted" else "⚠️"
        flags = doc.get("flags", [])

        details = {k: v for k, v in doc.items() if k not in ("doc_type", "status", "flags")}
        details_str = " &nbsp;·&nbsp; ".join(f"<b>{k.replace('_',' ').title()}:</b> {v}" for k, v in details.items())

        flag_html = "".join(f'<span class="doc-flag">⚑ {f}</span><br>' for f in flags)

        st.markdown(
            f'<div class="doc-row">'
            f'<span class="doc-type">{icon} {doc_type}</span><br>'
            f'<span style="font-size:0.8rem;color:#475569">{details_str}</span>'
            f'{"<br>" + flag_html if flags else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── Intelligence tab ───────────────────────────────────────────────────────────
def render_intelligence(case: dict) -> None:
    intel = case["intelligence"]

    st.markdown("**News & Open-Source Intelligence**")
    for item in intel["news_items"]:
        relevance_class = item["relevance"].lower()
        st.markdown(
            f'<div class="news-item {relevance_class}">'
            f'<div class="news-source">{item["source"]} — {item["date"]} &nbsp;'
            f'{risk_badge_html(item["relevance"])}</div>'
            f'<div class="news-headline">{item["headline"]}</div>'
            f'<div class="news-snippet">{item["snippet"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("**Transaction Pattern Analysis**")
    tp = intel["transaction_patterns"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Expected Monthly Vol", tp["expected_monthly_volume"])
    c2.metric("Counterparty Countries", ", ".join(tp["counterparty_countries"]))
    c3.metric("Velocity Flag", "YES" if tp["velocity_flag"] else "NO")

    if tp["velocity_flag"]:
        st.warning(f"**Velocity alert:** {tp['velocity_detail']}")
    st.info(f"**Funding source:** {tp['funding_source']}")


# ── AI Risk Analysis tab ───────────────────────────────────────────────────────
def render_ai_analysis(case: dict) -> None:
    st.markdown(
        '<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">'
        '<span style="font-size:1.1rem">🤖</span>'
        '<span style="font-size:0.75rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.5px;color:#0369a1">AI-Generated Risk Narrative</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="ai-narrative">{case["ai_narrative"].replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    ml = case["ml_scores"]
    st.markdown(
        f'<div class="card">'
        f'<div class="card-title">ML Model Output</div>'
        f'Recommendation: {risk_badge_html(ml["model_recommendation"].replace("_", " "), ml["model_recommendation"])}'
        f' &nbsp; Confidence: <b>{ml["model_confidence"]:.0%}</b>'
        f' &nbsp; Model: <code>{ml["model_version"]}</code>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Decision tab ───────────────────────────────────────────────────────────────
def render_decision(case: dict) -> None:
    case_id = case["case_id"]

    if f"submitted_{case_id}" not in st.session_state:
        st.session_state[f"submitted_{case_id}"] = False

    if st.session_state[f"submitted_{case_id}"]:
        st.success("Decision recorded. Case closed.")
        rec = st.session_state.get(f"record_{case_id}", {})
        st.json(rec)
        col1, _ = st.columns([1, 3])
        if col1.button("Download JSON", key=f"dl_{case_id}"):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w")
            json.dump(rec, tmp, indent=2)
            tmp.close()
            with open(tmp.name) as f:
                st.download_button("⬇️ Download", f.read(), file_name=f"{case_id}_decision.json", mime="application/json")
        return

    st.markdown('<div class="decision-header">Investigator Details</div>', unsafe_allow_html=True)
    reviewer = st.text_input("Your Name", placeholder="e.g. Sarah Mueller", key=f"reviewer_{case_id}")

    st.markdown('<div class="decision-header" style="margin-top:16px">Investigation Decision</div>', unsafe_allow_html=True)
    decision_label = st.radio(
        "Select outcome:",
        DECISION_OPTIONS,
        key=f"decision_{case_id}",
        index=None,
    )

    st.markdown('<div class="decision-header" style="margin-top:16px">Investigator Notes</div>', unsafe_allow_html=True)
    comment = st.text_area(
        "Rationale and supporting observations:",
        placeholder="Describe your findings, evidence reviewed, and reasoning for this decision…",
        height=120,
        key=f"comment_{case_id}",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    submit = st.button("Submit Decision", type="primary", key=f"submit_{case_id}")

    if submit:
        if not reviewer:
            st.error("Enter your name before submitting.")
        elif not decision_label:
            st.error("Select a decision before submitting.")
        else:
            decision_key = DECISION_KEYS[DECISION_OPTIONS.index(decision_label)]
            record = export_decision(case, decision_key, comment, reviewer)
            st.session_state[f"record_{case_id}"] = record
            st.session_state[f"submitted_{case_id}"] = True
            st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    case = render_sidebar()

    client_name = case["profile"].get("entity_name", "Unknown")
    case_id = case["case_id"]
    alert_type = case["alert_type"]
    risk_tier = case["risk_tier"]
    risk_score = case["risk_score"]
    badge = risk_badge_html(risk_tier, f"{risk_tier} RISK — {risk_score}/100")
    st.markdown(
        f'<div class="kyc-header">'
        f'<h1>KYC Risk Investigator</h1>'
        f'<p>Case <strong>{case_id}</strong> &nbsp;·&nbsp; '
        f'<strong>{client_name}</strong> &nbsp;·&nbsp; '
        f'{alert_type} &nbsp;·&nbsp; '
        f'{badge}'
        f'</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["👤 Profile", "⚠️ Risk Factors", "📄 Documents", "🔍 Intelligence", "🤖 AI Analysis", "✅ Decision"])

    with tabs[0]:
        render_profile(case)
    with tabs[1]:
        render_risk_factors(case)
    with tabs[2]:
        render_documents(case)
    with tabs[3]:
        render_intelligence(case)
    with tabs[4]:
        render_ai_analysis(case)
    with tabs[5]:
        render_decision(case)


if __name__ == "__main__":
    main()
