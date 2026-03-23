"""
Credit Memo SME Review — Gradio Version
===============================================
Structured human feedback app for AI-generated credit memos.
SMEs review each section, flag issues, edit content, and submit labeled
feedback for prompt refinement and fine-tuning.
"""

import copy
import json
import tempfile
import uuid
from datetime import datetime, timezone

import gradio as gr

from sample_data import SAMPLE_MEMO

# ── Constants ─────────────────────────────────────────────────────────────────
memo = SAMPLE_MEMO
memo_sections_by_id = {s["id"]: s for s in memo["sections"]}

FLAG_OPTIONS = {
    "incorrect_reasoning": ("🔴", "Incorrect Reasoning"),
    "policy_violation":    ("🟠", "Policy Violation"),
    "factual_error":       ("🔵", "Factual Error"),
    "missing_context":     ("🟢", "Missing Context"),
    "hallucination":       ("🟣", "Hallucination / Fabrication"),
    "overclaiming":        ("🟡", "Overclaiming / Overconfidence"),
}
FLAG_LABELS = [f"{icon} {label}" for _, (icon, label) in FLAG_OPTIONS.items()]
FLAG_KEYS   = list(FLAG_OPTIONS.keys())

RATING_OPTIONS = {
    "approve":            "✅ Approved as-is",
    "approve_with_edits": "✏️ Approved with edits",
    "needs_revision":     "⚠️ Needs Major Revision",
    "reject":             "❌ Reject / Incorrect",
}
RATING_LABELS = list(RATING_OPTIONS.values())
RATING_ICON   = {"approve": "✅", "approve_with_edits": "✏️", "needs_revision": "⚠️", "reject": "❌"}

REVIEWER_ROLES = [
    "Senior Credit Officer", "Credit Analyst", "Risk Manager",
    "Portfolio Manager", "Underwriter", "Compliance Officer", "Other",
]

OVERALL_QUALITY_OPTS = [
    "Excellent — minor or no issues",
    "Good — small improvements needed",
    "Adequate — several revisions required",
    "Poor — major rework needed",
]

ALIGN_OPTS = [
    "Yes — I agree with the model's decision",
    "No — I would APPROVE instead",
    "No — I would REJECT instead",
    "Refer to committee for further review",
]

# ── State helpers ─────────────────────────────────────────────────────────────
def make_initial_state() -> dict:
    return {
        "review_id": str(uuid.uuid4())[:8].upper(),
        "reviewer_name": "",
        "reviewer_role": "",
        "overall_rating": None,
        "final_decision_align": None,
        "overall_comment": "",
        "submitted": False,
        "sections": {
            s["id"]: {
                "rating": None,
                "flags": [],
                "edited_text": s["generated_text"],
                "comment": "",
                "reviewed": False,
            }
            for s in memo["sections"]
        },
    }


def flag_keys_from_labels(selected: list) -> list:
    return [k for k, (icon, label) in FLAG_OPTIONS.items() if f"{icon} {label}" in (selected or [])]


def rating_key_from_label(label_str):
    if not label_str:
        return None
    for k, v in RATING_OPTIONS.items():
        if v == label_str:
            return k
    return None


def render_progress_md(state: dict) -> str:
    total    = len(memo["sections"])
    reviewed = sum(1 for fb in state["sections"].values() if fb["reviewed"])
    lines = [f"**Progress: {reviewed}/{total} sections**\n"]
    for s in memo["sections"]:
        fb = state["sections"][s["id"]]
        status = RATING_ICON.get(fb["rating"], "✅") if fb["reviewed"] else "○"
        lines.append(f"{status} {s['icon']} {s['title']}")
    return "\n\n".join(lines)


# ── Data compilation ──────────────────────────────────────────────────────────
def compile_feedback(state: dict) -> dict:
    sections_out = []
    for s in memo["sections"]:
        sid = s["id"]
        fb  = state["sections"][sid]
        has_edits = fb["edited_text"].strip() != s["generated_text"].strip()
        sections_out.append({
            "section_id":    sid,
            "section_title": s["title"],
            "original_text": s["generated_text"],
            "edited_text":   fb["edited_text"],
            "has_edits":     has_edits,
            "rating":        fb["rating"],
            "flags":         fb["flags"],
            "comment":       fb["comment"],
            "reviewed":      fb["reviewed"],
            "sources":       s.get("sources", []),
        })
    return {
        "schema_version":        "1.0",
        "review_id":             state["review_id"],
        "memo_id":               memo["memo_id"],
        "borrower_name":         memo["borrower"]["name"],
        "reviewer_name":         state["reviewer_name"],
        "reviewer_role":         state["reviewer_role"],
        "timestamp_utc":         datetime.now(timezone.utc).isoformat(),
        "ml_model_version":      memo["ml_model_scores"]["model_version"],
        "ml_model_decision":     memo["ml_model_scores"]["model_decision"],
        "overall_rating":        state["overall_rating"],
        "final_decision_alignment": state["final_decision_align"],
        "overall_comment":       state["overall_comment"],
        "sections":              sections_out,
    }


def to_finetune_jsonl(feedback: dict) -> str:
    borrower = memo["borrower"]
    scores   = memo["ml_model_scores"]
    loan     = memo["loan_request"]
    lines = []
    for s_fb in feedback["sections"]:
        entry = {
            "type":           "credit_memo_section_feedback",
            "memo_id":        feedback["memo_id"],
            "review_id":      feedback["review_id"],
            "reviewer_role":  feedback["reviewer_role"],
            "section_id":     s_fb["section_id"],
            "section_title":  s_fb["section_title"],
            "borrower_context": {
                "name":           borrower["name"],
                "industry":       borrower["industry"],
                "loan_amount_usd": loan["amount"],
                "ml_decision":    scores["model_decision"],
                "pd":             scores["probability_of_default"],
                "lgd":            scores["loss_given_default"],
                "risk_grade":     scores["risk_grade"],
            },
            "sources_cited":         s_fb["sources"],
            "generated_output":      s_fb["original_text"],
            "sme_corrected_output":  s_fb["edited_text"] if s_fb["has_edits"] else None,
            "has_sme_edits":         s_fb["has_edits"],
            "rating":                s_fb["rating"],
            "flags":                 s_fb["flags"],
            "sme_comment":           s_fb["comment"],
            "is_reviewed":           s_fb["reviewed"],
        }
        lines.append(json.dumps(entry, ensure_ascii=False))
    return "\n".join(lines)


def make_summary_rows(state: dict) -> list:
    rows = []
    for s in memo["sections"]:
        fb  = state["sections"][s["id"]]
        r   = fb["rating"]
        rows.append([
            f"{s['icon']} {s['title']}",
            f"{RATING_ICON.get(r, '—')} {r}" if r else "— not rated",
            ", ".join(FLAG_OPTIONS[f][1] for f in fb["flags"]) if fb["flags"] else "None",
            "Yes" if fb["edited_text"].strip() != s["generated_text"].strip() else "—",
            "Reviewed" if fb["reviewed"] else "Pending",
        ])
    return rows


# ── Styling ───────────────────────────────────────────────────────────────────
CSS = """
/* ── Reset theme variables to light values ──────── */
:root, .gradio-container {
    --body-background-fill: #f4f6f9;
    --body-text-color: #1e293b;
    --body-text-color-subdued: #64748b;
    --border-color-primary: #e2e8f0;
    --background-fill-primary: #ffffff;
    --background-fill-secondary: #f8fafc;
    --block-background-fill: #f8fafc;
    --block-border-color: #e2e8f0;
    --block-border-width: 1px;
    --input-background-fill: #ffffff;
    --input-border-color: #cbd5e1;
    --input-placeholder-color: #94a3b8;
    --color-accent: #0f4c81;
    --button-primary-background-fill: #0f4c81;
    --button-primary-text-color: #ffffff;
    --button-secondary-background-fill: #ffffff;
    --button-secondary-text-color: #374151;
    --button-secondary-border-color: #d1d5db;
    --block-label-text-color: #374151;
    --block-title-text-color: #1e293b;
}

/* ── Block containers (radio, checkbox, textbox wrappers) */
.block {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 14px !important;
}

/* ── Global ─────────────────────────────────────── */
.gradio-container {
    max-width: 1440px !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}

/* ── Inputs: force white bg + dark text ─────────── */
input, textarea, select,
.block input, .block textarea,
.block input[type="text"], .block input[type="search"] {
    background-color: #ffffff !important;
    color: #1e293b !important;
    border-color: #cbd5e1 !important;
}
input::placeholder, textarea::placeholder { color: #94a3b8 !important; }

/* ── All label / span text inside blocks ────────── */
.block span,
.block label span,
.block .label-wrap span,
fieldset span,
.wrap span {
    color: #374151 !important;
}

/* ── Header banner ──────────────────────────────── */
.portal-header {
    background: linear-gradient(135deg, #1a2e4a 0%, #0f4c81 100%);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 16px;
}
.portal-header h1 { color: #ffffff !important; margin: 0 0 6px 0; font-size: 1.5rem; font-weight: 700; }
.portal-header p  { color: #b8cce4 !important; margin: 0; font-size: 0.88rem; }
.portal-header strong { color: #dbeafe !important; }

/* ── Left sidebar ───────────────────────────────── */
.left-panel {
    background: #ffffff !important;
    border-radius: 12px !important;
    padding: 20px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}

/* ── Main content card ──────────────────────────── */
.main-card {
    background: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    overflow: hidden !important;
}

/* ── Tabs ────────────────────────────────────────── */
.tabs > .tab-nav {
    background: #f8fafc !important;
    border-bottom: 2px solid #e2e8f0 !important;
    padding: 0 8px !important;
}
.tabs > .tab-nav button {
    color: #64748b !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    padding: 10px 14px !important;
    background: transparent !important;
    border: none !important;
}
.tabs > .tab-nav button.selected {
    color: #0f4c81 !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #0f4c81 !important;
    background: transparent !important;
}

/* ── Buttons ─────────────────────────────────────── */
button.primary, .primary {
    background: #0f4c81 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
button.secondary, .secondary {
    background: #ffffff !important;
    color: #374151 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
}

/* ── ML Score chips ──────────────────────────────── */
.score-chip {
    display: inline-flex;
    align-items: center;
    background: #f1f5f9;
    border: 1px solid #cbd5e1;
    border-radius: 20px;
    padding: 6px 14px;
    margin: 3px;
    font-size: 0.84rem;
    font-weight: 500;
    color: #334155;
}
.score-chip b { margin-left: 4px; }
.score-chip.pass   { background: #f0fdf4; border-color: #86efac; color: #166534; }
.score-chip.fail   { background: #fef2f2; border-color: #fca5a5; color: #991b1b; }
.score-chip.warn   { background: #fffbeb; border-color: #fcd34d; color: #92400e; }
.score-chip.approve {
    background: #f0fdf4;
    border: 2px solid #22c55e;
    color: #15803d;
    font-weight: 700;
    padding: 7px 18px;
}

/* ── Sources callout ─────────────────────────────── */
.sources-note {
    background: #eff6ff;
    border-left: 4px solid #60a5fa;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.83rem;
    color: #1e40af;
    margin-bottom: 10px;
}

/* ── Edit detected note ──────────────────────────── */
.edit-note {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 0.84rem;
    color: #166534;
    margin: 6px 0;
}

/* ── Section headings (Final Assessment) ─────────── */
.section-heading {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin: 16px 0 8px 0;
}
.section-divider {
    border-top: 1px solid #e2e8f0;
    margin: 20px 0 4px 0;
}

/* ── ML Decision badge ───────────────────────────── */
.decision-badge {
    display: flex;
    flex-direction: column;
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.decision-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #64748b;
    margin-bottom: 4px;
}
.decision-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: #15803d;
}
.decision-conf {
    font-size: 0.8rem;
    color: #4ade80;
    margin-top: 2px;
}

/* ── Progress tracker ────────────────────────────── */
.progress-tracker p,
.progress-tracker span { color: #1e293b !important; font-size: 0.87rem !important; line-height: 1.8 !important; }

/* ── Radio & Checkbox color ──────────────────────── */
input[type=radio], input[type=checkbox] {
    accent-color: #0f4c81 !important;
}
"""

# ── Build UI ──────────────────────────────────────────────────────────────────
def build_demo() -> gr.Blocks:
    b  = memo["borrower"]
    lr = memo["loan_request"]
    sc = memo["ml_model_scores"]
    dec_icon = "🟢" if sc["model_decision"] == "APPROVE" else "🔴"

    # Pre-build the ML score HTML for the overview
    def _chip(label, value, cls):
        return f'<span class="score-chip {cls}">{label}: <b>{value}</b></span>'

    scores_html = (
        '<div style="display:flex;flex-wrap:wrap;gap:4px;padding:4px 0 12px 0;">'
        + _chip("PD",    f"{sc['probability_of_default']:.1%}",
                "pass" if sc['probability_of_default'] < sc['pd_threshold'] else "fail")
        + _chip("LGD",   f"{sc['loss_given_default']:.1%}",
                "pass" if sc['loss_given_default'] < sc['lgd_threshold'] else "fail")
        + _chip("EL",    f"{sc['expected_loss']:.2%}",
                "pass" if sc['expected_loss'] < sc['el_threshold'] else "fail")
        + _chip("Risk Grade", sc['risk_grade'], "warn")
        + f'<span class="score-chip approve">{dec_icon} {sc["model_decision"]} '
          f'({sc["model_confidence"]:.0%} confidence)</span>'
        + '</div>'
    )

    with gr.Blocks(
        title="Credit Memo SME Review",
        theme=gr.themes.Soft(),
        css=CSS,
    ) as demo:

        state = gr.State(make_initial_state())

        # ── Header banner ──────────────────────────────────────────────────
        gr.HTML(
            f'<div class="portal-header">'
            f'<h1>🏦 Credit Memo SME Review Portal</h1>'
            f'<p>'
            f'<strong>Memo:</strong> {memo["memo_id"]} &nbsp;·&nbsp; '
            f'<strong>Borrower:</strong> {b["name"]} &nbsp;·&nbsp; '
            f'<strong>Facility:</strong> ${memo["loan_request"]["amount"]:,.0f} Senior Secured &nbsp;·&nbsp; '
            f'<strong>Generated:</strong> {memo["created_at"][:10]}'
            f'</p>'
            f'</div>'
        )

        with gr.Row(equal_height=False):

            # ── Left panel ────────────────────────────────────────────────────
            with gr.Column(scale=1, min_width=240, elem_classes="left-panel"):
                gr.Markdown("### Reviewer")
                reviewer_name_box = gr.Textbox(
                    label="Your Name",
                    placeholder="e.g. Jane Smith",
                    show_label=True,
                )
                reviewer_role_dd = gr.Dropdown(
                    label="Your Role",
                    choices=REVIEWER_ROLES,
                    value=None,
                )
                gr.Markdown("---")
                progress_md = gr.Markdown(
                    render_progress_md(make_initial_state()),
                    elem_classes="progress-tracker",
                )

            # ── Main content ──────────────────────────────────────────────────
            with gr.Column(scale=5, elem_classes="main-card"):
                with gr.Tabs():

                    # ── Overview ──────────────────────────────────────────────
                    with gr.Tab("📋 Overview"):
                        with gr.Row():
                            with gr.Column():
                                gr.HTML(
                                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px 20px;">'
                                    f'<div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin-bottom:10px;">Borrower</div>'
                                    f'<table style="width:100%;border-collapse:collapse;font-size:0.88rem;">'
                                    f'<tr><td style="color:#64748b;padding:4px 0;width:44%">Company</td><td style="color:#1e293b;font-weight:600">{b["name"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Industry</td><td style="color:#1e293b">{b["industry"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">NAICS</td><td style="color:#1e293b">{b["naics_code"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Headquarters</td><td style="color:#1e293b">{b["headquarters"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Years in Business</td><td style="color:#1e293b">{b["years_in_business"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Employees</td><td style="color:#1e293b">{b["employees"]:,}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Ownership</td><td style="color:#1e293b">{b["ownership"]}</td></tr>'
                                    f'</table></div>'
                                )
                            with gr.Column():
                                gr.HTML(
                                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px 20px;">'
                                    f'<div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin-bottom:10px;">Loan Request</div>'
                                    f'<table style="width:100%;border-collapse:collapse;font-size:0.88rem;">'
                                    f'<tr><td style="color:#64748b;padding:4px 0;width:44%">Total Facility</td><td style="color:#1e293b;font-weight:700;font-size:1rem">${lr["amount"]:,.0f}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Type</td><td style="color:#1e293b">{lr["type"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Term Loan</td><td style="color:#1e293b">${lr["term_loan_amount"]:,.0f}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Revolver</td><td style="color:#1e293b">${lr["revolver_amount"]:,.0f}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Term</td><td style="color:#1e293b">{lr["term"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Purpose</td><td style="color:#1e293b">{lr["purpose"]}</td></tr>'
                                    f'<tr><td style="color:#64748b;padding:4px 0">Collateral</td><td style="color:#1e293b">{lr["collateral"]}</td></tr>'
                                    f'</table></div>'
                                )
                        gr.HTML('<div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#64748b;margin:16px 0 8px 0;">ML Risk Model Scores</div>')
                        gr.HTML(scores_html)
                        gr.Markdown("---")
                        gr.Markdown(
                            "### How to use this tool\n\n"
                            "1. Enter your **name** and **role** in the left panel.\n"
                            "2. Click through the **section tabs** (Exec Summary → Recommendation).\n"
                            "3. For each section: read the AI-generated text, **edit** if needed, "
                            "select a **rating**, check applicable **flags**, and add a **comment**.\n"
                            "4. Click **✅ Mark as Reviewed** to save feedback for that section — "
                            "the progress tracker on the left updates.\n"
                            "5. Go to the **📤 Final Assessment** tab to submit and download "
                            "your labeled data as JSON or fine-tuning JSONL.\n\n"
                            "_Feedback creates labeled training data tied to real memo context — "
                            "used for prompt refinement and LLM fine-tuning._"
                        )

                    # ── Section tabs (one per memo section) ───────────────────
                    section_comps: dict[str, dict] = {}

                    for section in memo["sections"]:
                        sid       = section["id"]
                        orig_text = section["generated_text"]
                        sources   = " · ".join(section.get("sources", []))

                        with gr.Tab(f"{section['icon']} {section['title']}"):
                            if sources:
                                gr.HTML(f'<div class="sources-note">📎 <strong>Sources:</strong> {sources}</div>')

                            text_box = gr.Textbox(
                                value=orig_text,
                                label="AI-Generated Content — edit directly to correct errors or improve the text",
                                lines=18,
                                max_lines=40,
                            )

                            with gr.Row():
                                reset_btn = gr.Button("↩ Reset to original", size="sm", variant="secondary")
                            edit_note = gr.Markdown("")

                            rating_radio = gr.Radio(
                                choices=RATING_LABELS,
                                label="Section Rating",
                                value=None,
                            )

                            flags_cbg = gr.CheckboxGroup(
                                choices=FLAG_LABELS,
                                label="Flag Issues — check all that apply",
                                value=[],
                            )

                            comment_box = gr.Textbox(
                                label="Reviewer Comment",
                                placeholder=(
                                    "Explain your flags or edits. Be specific — e.g., "
                                    "'The pro forma DSCR uses TTM EBITDA rather than FY2023 audited figure. "
                                    "Correct value is 1.42x not 1.37x.' This comment feeds prompt-improvement notes."
                                ),
                                lines=3,
                            )

                            with gr.Row():
                                mark_btn = gr.Button("✅ Mark as Reviewed", variant="primary", scale=2)
                                skip_btn = gr.Button("⏭ Save draft / Skip", variant="secondary", scale=1)

                            status_md = gr.Markdown("")

                            section_comps[sid] = {
                                "text":      text_box,
                                "rating":    rating_radio,
                                "flags":     flags_cbg,
                                "comment":   comment_box,
                                "status":    status_md,
                                "mark_btn":  mark_btn,
                                "skip_btn":  skip_btn,
                                "reset_btn": reset_btn,
                                "edit_note": edit_note,
                            }

                    # ── Final Assessment / Submit ──────────────────────────────
                    with gr.Tab("📤 Final Assessment"):
                        gr.HTML('<div class="section-heading">Section Review Summary</div>')
                        refresh_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")
                        section_summary_df = gr.Dataframe(
                            headers=["Section", "Rating", "Flags", "Edits", "Status"],
                            label="",
                            interactive=False,
                            wrap=True,
                        )

                        gr.HTML('<div class="section-divider"></div>')
                        gr.HTML('<div class="section-heading">Overall Memo Quality</div>')
                        with gr.Row():
                            with gr.Column():
                                overall_quality = gr.Radio(
                                    choices=OVERALL_QUALITY_OPTS,
                                    label="How do you rate the overall quality of this AI-generated memo?",
                                    value=None,
                                )
                            with gr.Column():
                                gr.HTML(
                                    f'<div class="decision-badge">'
                                    f'<span class="decision-label">ML Model Decision</span>'
                                    f'<span class="decision-value">{dec_icon} {sc["model_decision"]}</span>'
                                    f'<span class="decision-conf">{sc["model_confidence"]:.0%} confidence</span>'
                                    f'</div>'
                                )
                                decision_align = gr.Radio(
                                    choices=ALIGN_OPTS,
                                    label="Do you agree with the ML model's credit decision?",
                                    value=None,
                                )

                        overall_comment_box = gr.Textbox(
                            label="Overall Comments",
                            placeholder=(
                                "Additional feedback on memo quality, model behavior, or process. "
                                "e.g., 'Financial analysis strong. Industry section underweighted EV transition risk — "
                                "recommend adding 20% revenue decline sensitivity analysis.'"
                            ),
                            lines=4,
                        )

                        submit_btn    = gr.Button("🚀 Submit Review", variant="primary", size="lg")
                        submit_status = gr.Markdown("")

                        gr.HTML('<div class="section-divider"></div>')
                        gr.HTML('<div class="section-heading">Download Labeled Data</div>')
                        gr.HTML(
                            '<div class="sources-note" style="margin-bottom:10px;">'
                            '📦 The JSONL file contains one record per section with original output, '
                            'SME-corrected output, rating, flags, and borrower context — '
                            'ready for supervised fine-tuning or RLHF reward model training.'
                            '</div>'
                        )
                        with gr.Row():
                            export_json_btn  = gr.Button("⬇️ Export Full JSON", variant="secondary")
                            export_jsonl_btn = gr.Button("⬇️ Export JSONL (Fine-tuning)", variant="secondary")

                        json_file  = gr.File(label="JSON Download",  visible=False)
                        jsonl_file = gr.File(label="JSONL Download", visible=False)

        # ── Event handlers ────────────────────────────────────────────────────
        # Factory functions avoid Python loop-closure capture issues.

        def _make_edit_note(orig: str):
            def fn(text: str) -> str:
                if text.strip() != orig.strip():
                    return "✏️ **Edits detected** — your corrections will be captured as labeled data."
                return ""
            return fn

        def _make_reset(orig: str):
            return lambda: orig

        def _make_mark(sid_: str):
            def fn(state_, text, rating_label, flags_labels, comment, name, role):
                state_ = copy.deepcopy(state_)
                state_["reviewer_name"] = (name or "").strip()
                state_["reviewer_role"] = role or ""

                rating_key = rating_key_from_label(rating_label)
                flag_keys  = flag_keys_from_labels(flags_labels)

                # Auto-upgrade approve → approve_with_edits when text is edited
                orig = memo_sections_by_id[sid_]["generated_text"]
                if rating_key == "approve" and text.strip() != orig.strip():
                    rating_key = "approve_with_edits"

                if not rating_key:
                    return (
                        state_,
                        "⚠️ **Select a rating before marking as reviewed.**",
                        render_progress_md(state_),
                    )

                state_["sections"][sid_] = {
                    "rating":      rating_key,
                    "flags":       flag_keys,
                    "edited_text": text,
                    "comment":     comment,
                    "reviewed":    True,
                }

                rating_str = RATING_OPTIONS.get(rating_key, "")
                msg = f"✅ **Marked as reviewed** — {rating_str}"
                if flag_keys:
                    flag_names = [FLAG_OPTIONS[k][1] for k in flag_keys]
                    msg += f"  \n🚩 Flags: {', '.join(flag_names)}"

                return state_, msg, render_progress_md(state_)
            return fn

        def _make_skip(sid_: str):
            def fn(state_, text, rating_label, flags_labels, comment, name, role):
                state_ = copy.deepcopy(state_)
                state_["reviewer_name"] = (name or "").strip()
                state_["reviewer_role"] = role or ""
                state_["sections"][sid_].update({
                    "rating":      rating_key_from_label(rating_label),
                    "flags":       flag_keys_from_labels(flags_labels),
                    "edited_text": text,
                    "comment":     comment,
                })
                return (
                    state_,
                    "⏭ Draft saved — section not yet marked as reviewed.",
                    render_progress_md(state_),
                )
            return fn

        for section in memo["sections"]:
            sid   = section["id"]
            comps = section_comps[sid]
            orig  = section["generated_text"]

            comps["text"].change(
                fn=_make_edit_note(orig),
                inputs=comps["text"],
                outputs=comps["edit_note"],
            )
            comps["reset_btn"].click(
                fn=_make_reset(orig),
                outputs=comps["text"],
            )
            comps["mark_btn"].click(
                fn=_make_mark(sid),
                inputs=[
                    state,
                    comps["text"], comps["rating"], comps["flags"], comps["comment"],
                    reviewer_name_box, reviewer_role_dd,
                ],
                outputs=[state, comps["status"], progress_md],
            )
            comps["skip_btn"].click(
                fn=_make_skip(sid),
                inputs=[
                    state,
                    comps["text"], comps["rating"], comps["flags"], comps["comment"],
                    reviewer_name_box, reviewer_role_dd,
                ],
                outputs=[state, comps["status"], progress_md],
            )

        # Refresh summary table
        def _refresh_summary(state_):
            return make_summary_rows(state_)

        refresh_btn.click(fn=_refresh_summary, inputs=state, outputs=section_summary_df)

        # Submit
        def _on_submit(state_, overall_rating, decision_align_, overall_comment, name, role):
            if not (name or "").strip():
                return state_, "❌ **Enter your name in the left panel before submitting.**", [], render_progress_md(state_)
            if not overall_rating:
                return state_, "❌ **Select an overall memo quality rating.**", [], render_progress_md(state_)
            if not decision_align_:
                return state_, "❌ **Indicate whether you agree with the model's credit decision.**", [], render_progress_md(state_)

            state_ = copy.deepcopy(state_)
            state_["reviewer_name"]       = name.strip()
            state_["reviewer_role"]       = role or ""
            state_["overall_rating"]      = overall_rating
            state_["final_decision_align"] = decision_align_
            state_["overall_comment"]     = overall_comment
            state_["submitted"]           = True

            reviewed = sum(1 for fb in state_["sections"].values() if fb["reviewed"])
            total    = len(memo["sections"])
            msg = (
                f"## ✅ Review Submitted!\n\n"
                f"**Review ID:** `{state_['review_id']}`  \n"
                f"**Reviewer:** {name.strip()} ({role})  \n"
                f"**Sections reviewed:** {reviewed}/{total}  \n"
                f"**Overall rating:** {overall_rating}  \n"
                f"**Decision alignment:** {decision_align_}  \n\n"
                f"Download your labeled data using the buttons below."
            )
            return state_, msg, make_summary_rows(state_), render_progress_md(state_)

        submit_btn.click(
            fn=_on_submit,
            inputs=[state, overall_quality, decision_align, overall_comment_box, reviewer_name_box, reviewer_role_dd],
            outputs=[state, submit_status, section_summary_df, progress_md],
        )

        # Export helpers — capture latest overall fields before exporting
        def _prep_state(state_, overall_rating, decision_align_, overall_comment, name, role):
            state_ = copy.deepcopy(state_)
            state_["reviewer_name"]        = (name or "").strip()
            state_["reviewer_role"]        = role or ""
            state_["overall_rating"]       = overall_rating
            state_["final_decision_align"] = decision_align_
            state_["overall_comment"]      = overall_comment
            return state_

        def _export_json(state_, overall_rating, decision_align_, overall_comment, name, role):
            state_    = _prep_state(state_, overall_rating, decision_align_, overall_comment, name, role)
            feedback  = compile_feedback(state_)
            json_str  = json.dumps(feedback, indent=2, ensure_ascii=False)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False,
                prefix=f"review_{memo['memo_id']}_",
            )
            tmp.write(json_str)
            tmp.close()
            return gr.update(value=tmp.name, visible=True)

        def _export_jsonl(state_, overall_rating, decision_align_, overall_comment, name, role):
            state_    = _prep_state(state_, overall_rating, decision_align_, overall_comment, name, role)
            feedback  = compile_feedback(state_)
            jsonl_str = to_finetune_jsonl(feedback)
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False,
                prefix=f"finetune_{memo['memo_id']}_",
            )
            tmp.write(jsonl_str)
            tmp.close()
            return gr.update(value=tmp.name, visible=True)

        _export_inputs = [state, overall_quality, decision_align, overall_comment_box, reviewer_name_box, reviewer_role_dd]
        export_json_btn.click(fn=_export_json,   inputs=_export_inputs, outputs=json_file)
        export_jsonl_btn.click(fn=_export_jsonl, inputs=_export_inputs, outputs=jsonl_file)

    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)