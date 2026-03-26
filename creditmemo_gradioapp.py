"""
Credit Memo SME Review Portal — Gradio Version
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
                "name":            borrower["name"],
                "industry":        borrower["industry"],
                "loan_amount_usd": loan["amount"],
                "ml_decision":     scores["model_decision"],
                "pd":              scores["probability_of_default"],
                "lgd":             scores["loss_given_default"],
                "risk_grade":      scores["risk_grade"],
            },
            "sources_cited":        s_fb["sources"],
            "generated_output":     s_fb["original_text"],
            "sme_corrected_output": s_fb["edited_text"] if s_fb["has_edits"] else None,
            "has_sme_edits":        s_fb["has_edits"],
            "rating":               s_fb["rating"],
            "flags":                s_fb["flags"],
            "sme_comment":          s_fb["comment"],
            "is_reviewed":          s_fb["reviewed"],
        }
        lines.append(json.dumps(entry, ensure_ascii=False))
    return "\n".join(lines)


# ── Styling ───────────────────────────────────────────────────────────────────
CSS = """
.gradio-container { max-width: 1440px !important; }
.left-panel { background: #f8f9fa; border-radius: 10px; padding: 16px; border: 1px solid #dee2e6; }
.score-chip {
    display: inline-block; background: #e9ecef; border-radius: 8px;
    padding: 8px 14px; margin: 4px; font-size: 0.9em; font-weight: 500;
}
.score-chip.pass    { background: #d4edda; color: #155724; }
.score-chip.warn    { background: #fff3cd; color: #856404; }
.score-chip.fail    { background: #f8d7da; color: #721c24; }
.score-chip.approve { background: #cce5ff; color: #004085; font-weight: 700; }
.edit-note {
    background: #d1f0c2; border-left: 4px solid #28a745;
    padding: 6px 12px; border-radius: 4px; font-size: 0.88em;
    color: #155724; margin: 6px 0;
}
.status-ok   { color: #155724; font-weight: 600; }
.status-warn { color: #856404; font-weight: 600; }
.status-err  { color: #721c24; font-weight: 600; }
"""

# ── Build UI ──────────────────────────────────────────────────────────────────
def build_demo() -> gr.Blocks:
    b  = memo["borrower"]
    lr = memo["loan_request"]
    sc = memo["ml_model_scores"]
    dec_icon = "🟢" if sc["model_decision"] == "APPROVE" else "🔴"

    def _chip(label, value, ok):
        cls = "pass" if ok else "fail"
        return f'<span class="score-chip {cls}">{label}: <b>{value}</b></span>'

    scores_html = (
        '<div style="line-height:2.4">'
        + _chip("PD",   f"{sc['probability_of_default']:.1%}", sc['probability_of_default'] < sc['pd_threshold'])
        + _chip("LGD",  f"{sc['loss_given_default']:.1%}",    sc['loss_given_default']      < sc['lgd_threshold'])
        + _chip("EL",   f"{sc['expected_loss']:.2%}",         sc['expected_loss']            < sc['el_threshold'])
        + _chip("Grade", sc['risk_grade'], True)
        + f'<span class="score-chip approve">{dec_icon} {sc["model_decision"]} '
          f'({sc["model_confidence"]:.0%} confidence)</span>'
        + '</div>'
    )

    with gr.Blocks(
        title="Credit Memo SME Review",
        theme=gr.themes.Soft(primary_hue="blue", neutral_hue="slate"),
        css=CSS,
    ) as demo:

        state = gr.State(make_initial_state())

        gr.Markdown(
            f"# 🏦 Credit Memo SME Review Portal\n"
            f"**Memo:** \`{memo['memo_id']}\` &nbsp;·&nbsp; "
            f"**Borrower:** {b['name']} &nbsp;·&nbsp; "
            f"**Generated:** {memo['created_at'][:10]}"
        )

        with gr.Row():
            with gr.Column(scale=1, min_width=230, elem_classes="left-panel"):
                gr.Markdown("### Reviewer")
                reviewer_name_box = gr.Textbox(label="Your Name", placeholder="e.g. Jane Smith")
                reviewer_role_dd  = gr.Dropdown(label="Your Role", choices=REVIEWER_ROLES, value=None)
                gr.Markdown("---")
                progress_md = gr.Markdown(render_progress_md(make_initial_state()))

            with gr.Column(scale=5):
                with gr.Tabs():
                    with gr.Tab("📋 Overview"):
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown(
                                    f"### Borrower\n"
                                    f"- **Company:** {b['name']}\n"
                                    f"- **Industry:** {b['industry']} (NAICS {b['naics_code']})\n"
                                    f"- **HQ:** {b['headquarters']}\n"
                                    f"- **Years in Business:** {b['years_in_business']}\n"
                                    f"- **Employees:** {b['employees']:,}\n"
                                    f"- **Ownership:** {b['ownership']}"
                                )
                            with gr.Column():
                                gr.Markdown(
                                    f"### Loan Request\n"
                                    f"- **Total Facility:** \${lr['amount']:,.0f}\n"
                                    f"- **Type:** {lr['type']}\n"
                                    f"- **Term:** {lr['term']}\n"
                                    f"- **Purpose:** {lr['purpose']}\n"
                                    f"- **Collateral:** {lr['collateral']}"
                                )
                        gr.Markdown("### ML Risk Model Scores")
                        gr.HTML(scores_html)

                    section_comps: dict[str, dict] = {}

                    for section in memo["sections"]:
                        sid       = section["id"]
                        orig_text = section["generated_text"]
                        sources   = " · ".join(section.get("sources", []))

                        with gr.Tab(f"{section['icon']} {section['title']}"):
                            if sources:
                                gr.Markdown(f"_**Sources:** {sources}_")
                            text_box = gr.Textbox(
                                value=orig_text,
                                label="AI-Generated Content — edit directly to correct errors",
                                lines=18, max_lines=40,
                            )
                            with gr.Row():
                                reset_btn = gr.Button("↩ Reset to original", size="sm", variant="secondary")
                            edit_note    = gr.Markdown("")
                            rating_radio = gr.Radio(choices=RATING_LABELS, label="Section Rating", value=None)
                            flags_cbg    = gr.CheckboxGroup(choices=FLAG_LABELS, label="Flag Issues", value=[])
                            comment_box  = gr.Textbox(label="Reviewer Comment", lines=3)
                            with gr.Row():
                                mark_btn = gr.Button("✅ Mark as Reviewed", variant="primary", scale=2)
                                skip_btn = gr.Button("⏭ Save draft / Skip",  variant="secondary", scale=1)
                            status_md = gr.Markdown("")
                            section_comps[sid] = {
                                "text": text_box, "rating": rating_radio, "flags": flags_cbg,
                                "comment": comment_box, "status": status_md,
                                "mark_btn": mark_btn, "skip_btn": skip_btn,
                                "reset_btn": reset_btn, "edit_note": edit_note,
                            }

                    with gr.Tab("📤 Final Assessment"):
                        refresh_btn        = gr.Button("🔄 Refresh Summary", variant="secondary", size="sm")
                        section_summary_df = gr.Dataframe(
                            headers=["Section", "Rating", "Flags", "Edits", "Status"],
                            label="Section Review Summary", interactive=False, wrap=True,
                        )
                        gr.Markdown("### Overall Memo Quality")
                        with gr.Row():
                            with gr.Column():
                                overall_quality = gr.Radio(choices=OVERALL_QUALITY_OPTS,
                                    label="How do you rate the overall quality?", value=None)
                            with gr.Column():
                                decision_align = gr.Radio(choices=ALIGN_OPTS,
                                    label="Do you agree with the ML model's credit decision?", value=None)
                        overall_comment_box = gr.Textbox(label="Overall Comments", lines=4)
                        submit_btn    = gr.Button("🚀 Submit Review", variant="primary", size="lg")
                        submit_status = gr.Markdown("")
                        gr.Markdown("### Download Labeled Data")
                        with gr.Row():
                            export_json_btn  = gr.Button("⬇️ Export Full JSON",             variant="secondary")
                            export_jsonl_btn = gr.Button("⬇️ Export JSONL (Fine-tuning)", variant="secondary")
                        json_file  = gr.File(label="JSON Download",  visible=False)
                        jsonl_file = gr.File(label="JSONL Download", visible=False)

        # ── Event handlers ────────────────────────────────────────────────────
        def _make_edit_note(orig):
            def fn(text):
                return "✏️ **Edits detected** — corrections captured as labeled data." \
                    if text.strip() != orig.strip() else ""
            return fn

        def _make_reset(orig):
            return lambda: orig

        def _make_mark(sid_):
            def fn(state_, text, rating_label, flags_labels, comment, name, role):
                state_ = copy.deepcopy(state_)
                state_["reviewer_name"] = (name or "").strip()
                state_["reviewer_role"] = role or ""
                rating_key = rating_key_from_label(rating_label)
                flag_keys  = flag_keys_from_labels(flags_labels)
                orig = memo_sections_by_id[sid_]["generated_text"]
                if rating_key == "approve" and text.strip() != orig.strip():
                    rating_key = "approve_with_edits"
                if not rating_key:
                    return state_, "⚠️ **Select a rating before marking as reviewed.**", render_progress_md(state_)
                state_["sections"][sid_] = {
                    "rating": rating_key, "flags": flag_keys,
                    "edited_text": text, "comment": comment, "reviewed": True,
                }
                msg = f"✅ **Marked as reviewed** — {RATING_OPTIONS.get(rating_key, '')}"
                if flag_keys:
                    msg += f"  \n🚩 Flags: {', '.join(FLAG_OPTIONS[k][1] for k in flag_keys)}"
                return state_, msg, render_progress_md(state_)
            return fn

        def _make_skip(sid_):
            def fn(state_, text, rating_label, flags_labels, comment, name, role):
                state_ = copy.deepcopy(state_)
                state_["reviewer_name"] = (name or "").strip()
                state_["reviewer_role"] = role or ""
                state_["sections"][sid_].update({
                    "rating": rating_key_from_label(rating_label),
                    "flags": flag_keys_from_labels(flags_labels),
                    "edited_text": text, "comment": comment,
                })
                return state_, "⏭ Draft saved.", render_progress_md(state_)
            return fn

        for section in memo["sections"]:
            sid, comps, orig = section["id"], section_comps[section["id"]], section["generated_text"]
            comps["text"].change(fn=_make_edit_note(orig), inputs=comps["text"], outputs=comps["edit_note"])
            comps["reset_btn"].click(fn=_make_reset(orig), outputs=comps["text"])
            comps["mark_btn"].click(fn=_make_mark(sid),
                inputs=[state, comps["text"], comps["rating"], comps["flags"], comps["comment"],
                        reviewer_name_box, reviewer_role_dd],
                outputs=[state, comps["status"], progress_md])
            comps["skip_btn"].click(fn=_make_skip(sid),
                inputs=[state, comps["text"], comps["rating"], comps["flags"], comps["comment"],
                        reviewer_name_box, reviewer_role_dd],
                outputs=[state, comps["status"], progress_md])

        refresh_btn.click(fn=lambda s: make_summary_rows(s), inputs=state, outputs=section_summary_df)

        def _on_submit(state_, overall_rating, decision_align_, overall_comment, name, role):
            if not (name or "").strip():
                return state_, "❌ **Enter your name before submitting.**", [], render_progress_md(state_)
            if not overall_rating:
                return state_, "❌ **Select an overall memo quality rating.**", [], render_progress_md(state_)
            state_ = copy.deepcopy(state_)
            state_.update({"reviewer_name": name.strip(), "reviewer_role": role or "",
                           "overall_rating": overall_rating, "final_decision_align": decision_align_,
                           "overall_comment": overall_comment, "submitted": True})
            reviewed = sum(1 for fb in state_["sections"].values() if fb["reviewed"])
            total    = len(memo["sections"])
            msg = (f"## ✅ Review Submitted!\n\n"
                   f"**Review ID:** \`{state_['review_id']}\`  \n"
                   f"**Reviewer:** {name.strip()} ({role})  \n"
                   f"**Sections reviewed:** {reviewed}/{total}  \n"
                   f"**Decision alignment:** {decision_align_}  \n\n"
                   f"Download your labeled data below.")
            return state_, msg, make_summary_rows(state_), render_progress_md(state_)

        submit_btn.click(fn=_on_submit,
            inputs=[state, overall_quality, decision_align, overall_comment_box, reviewer_name_box, reviewer_role_dd],
            outputs=[state, submit_status, section_summary_df, progress_md])

        def _prep(state_, oq, da, oc, name, role):
            state_ = copy.deepcopy(state_)
            state_.update({"reviewer_name": (name or "").strip(), "reviewer_role": role or "",
                           "overall_rating": oq, "final_decision_align": da, "overall_comment": oc})
            return state_

        def _export_json(state_, oq, da, oc, name, role):
            fb = compile_feedback(_prep(state_, oq, da, oc, name, role))
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, prefix=f"review_{memo['memo_id']}_")
            tmp.write(json.dumps(fb, indent=2, ensure_ascii=False)); tmp.close()
            return gr.File(value=tmp.name, visible=True)

        def _export_jsonl(state_, oq, da, oc, name, role):
            fb = compile_feedback(_prep(state_, oq, da, oc, name, role))
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, prefix=f"finetune_{memo['memo_id']}_")
            tmp.write(to_finetune_jsonl(fb)); tmp.close()
            return gr.File(value=tmp.name, visible=True)

        _ei = [state, overall_quality, decision_align, overall_comment_box, reviewer_name_box, reviewer_role_dd]
        export_json_btn.click(fn=_export_json,   inputs=_ei, outputs=json_file)
        export_jsonl_btn.click(fn=_export_jsonl, inputs=_ei, outputs=jsonl_file)

    return demo


demo = build_demo()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
