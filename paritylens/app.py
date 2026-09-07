"""ParityLens reviewer UI — hackathon prototype."""

from __future__ import annotations

import base64
import csv
import io
import sys
from datetime import datetime
from pathlib import Path

# Allow running this Streamlit script directly from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from paritylens.engine.pipeline import load_paper_csv, run_pipeline
from paritylens.eval.evaluate import compare_configs, evaluate_with_ground_truth

st.set_page_config(page_title="ParityLens", page_icon="🔍", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
DEMO_PATH = DATA_DIR / "demo_paper.csv"
BENCH_PATH = DATA_DIR / "benchmark.csv"


# -----------------------------------------------------------------------------
# Session state helpers
# -----------------------------------------------------------------------------

def init_state():
    defaults = {
        "results": None,
        "df": None,
        "decisions": {},  # id -> {"status": "accepted"/"rejected"/"pending", "notes": ""}
        "current_config": "hybrid",
        "semantic_threshold": 0.45,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# -----------------------------------------------------------------------------
# UI helpers
# -----------------------------------------------------------------------------

def severity_color(sev: str) -> str:
    return {"high": "🔴", "medium": "🟠", "low": "🟡"}.get(sev, "⚪")


def download_link(data: bytes, filename: str, label: str) -> str:
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'


def build_pdf_report(results, decisions, paper_name: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>ParityLens QA Report</b>", styles["Title"]))
    story.append(Paragraph(f"Paper: {paper_name}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    total = len(results)
    flagged = sum(1 for r in results if r.is_flagged)
    accepted = sum(1 for d in decisions.values() if d.get("status") == "accepted")
    rejected = sum(1 for d in decisions.values() if d.get("status") == "rejected")

    story.append(Paragraph(f"Total questions: {total}", styles["Normal"]))
    story.append(Paragraph(f"Flagged by engine: {flagged}", styles["Normal"]))
    story.append(Paragraph(f"Reviewer accepted: {accepted} | Rejected: {rejected} | Pending: {flagged - accepted - rejected}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    for r in results:
        if not r.is_flagged:
            continue
        dec = decisions.get(r.id, {})
        story.append(Paragraph(f"<b>Q{r.question_number} ({r.id})</b>", styles["Heading2"]))
        story.append(Paragraph(f"Decision: <b>{dec.get('status', 'pending')}</b>", styles["Normal"]))
        story.append(Paragraph(f"Reviewer notes: {dec.get('notes', '')}", styles["Normal"]))
        story.append(Paragraph("English: " + r.english[:300], styles["Normal"]))
        story.append(Paragraph("Urdu: " + r.urdu[:300], styles["Normal"]))
        data = [["Category", "Severity", "Confidence", "Evidence"]]
        for f in r.all_flags:
            data.append([f["category"], f["severity"], f"{f['confidence']:.2f}", f["message"][:200]])
        t = Table(data, colWidths=[1.5 * inch, 0.8 * inch, 0.8 * inch, 3 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.15 * inch))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

st.sidebar.title("ParityLens 🔍")
st.sidebar.caption("Bilingual exam parity auditor")
page = st.sidebar.radio("Go to", ["Demo", "Reviewer Queue", "Benchmark", "Help"])

config = st.sidebar.selectbox("Pipeline mode", ["hybrid", "rules", "semantic"], index=0)
threshold = st.sidebar.slider("Semantic threshold", 0.0, 1.0, 0.45, 0.05)
st.session_state.current_config = config
st.session_state.semantic_threshold = threshold

# -----------------------------------------------------------------------------
# Demo page
# -----------------------------------------------------------------------------

if page == "Demo":
    st.header("Upload a bilingual paper")
    st.info("PDF/image OCR is stubbed in this prototype. Upload a CSV with columns: id, question_number, english, urdu, true_mismatch (optional).")

    # Persist the selected upload across reruns so the "Run parity check" button
    # keeps working after the user clicks it.
    if "uploaded_path" not in st.session_state:
        st.session_state.uploaded_path = None
        st.session_state.uploaded_name = ""

    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("Upload paper CSV", type=["csv"])
    with col2:
        st.write("Or use the built-in demo paper:")
        if st.button("Load 20-question demo paper"):
            st.session_state.uploaded_path = DEMO_PATH
            st.session_state.uploaded_name = DEMO_PATH.name

    if uploaded is not None:
        st.session_state.uploaded_path = io.StringIO(uploaded.getvalue().decode("utf-8-sig"))
        st.session_state.uploaded_name = uploaded.name

    if st.session_state.uploaded_path:
        path = st.session_state.uploaded_path
        if isinstance(path, Path):
            df = load_paper_csv(str(path))
        else:
            df = load_paper_csv(path)
        paper_name = st.session_state.uploaded_name

        st.session_state.df = df
        st.write(f"Loaded **{len(df)}** question pairs from `{paper_name}`.")

        if st.button("Run parity check", type="primary"):
            with st.spinner("Running deterministic + semantic checks..."):
                results = run_pipeline(df, config=config, semantic_threshold=threshold)
            st.session_state.results = results
            st.session_state.decisions = {}
            st.success(f"Checked {len(results)} pairs in ~{sum(r.elapsed_ms for r in results):.0f} ms.")

    if st.session_state.results:
        results = st.session_state.results
        flagged = [r for r in results if r.is_flagged]
        clean = [r for r in results if not r.is_flagged]

        st.subheader("Risk summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total questions", len(results))
        c2.metric("Flagged", len(flagged))
        c3.metric("Clean", len(clean))
        c4.metric("Avg latency (ms)", round(sum(r.elapsed_ms for r in results) / len(results), 1))

        if flagged:
            st.subheader("Flagged questions")
            for r in flagged:
                with st.expander(f"Q{r.question_number} — {len(r.all_flags)} flag(s) (risk {r.risk_score:.2f})"):
                    cols = st.columns(2)
                    with cols[0]:
                        st.markdown("**English**")
                        st.write(r.english)
                    with cols[1]:
                        st.markdown("**Urdu / اردو**")
                        st.write(r.urdu)
                    st.markdown("**Evidence**")
                    for f in r.all_flags:
                        st.markdown(
                            f"{severity_color(f['severity'])} **{f['category']}** ({f['source']}) — "
                            f"confidence {f['confidence']:.2f}\n\n{f['message']}"
                        )
                        st.caption(f"EN: {f['en_evidence'][:120]} | UR: {f['ur_evidence'][:120]}")

# -----------------------------------------------------------------------------
# Reviewer Queue page
# -----------------------------------------------------------------------------

elif page == "Reviewer Queue":
    st.header("Reviewer queue")
    if not st.session_state.results:
        st.warning("Run a parity check first from the Demo page.")
        st.stop()

    results = st.session_state.results
    flagged = [r for r in results if r.is_flagged]

    if not flagged:
        st.success("No flags to review.")
        st.stop()

    progress = st.progress(0)
    reviewed = sum(1 for d in st.session_state.decisions.values() if d.get("status") in ("accepted", "rejected"))
    progress.progress(min(reviewed / len(flagged), 1.0))

    for idx, r in enumerate(flagged):
        dec = st.session_state.decisions.setdefault(r.id, {"status": "pending", "notes": ""})
        with st.container(border=True):
            st.subheader(f"Q{r.question_number} — {r.id}")
            cols = st.columns([1, 1, 1])
            with cols[0]:
                st.markdown("**English**")
                st.write(r.english)
            with cols[1]:
                st.markdown("**Urdu / اردو**")
                st.write(r.urdu)
            with cols[2]:
                st.markdown("**Evidence panel**")
                for f in r.all_flags:
                    st.markdown(
                        f"{severity_color(f['severity'])} **{f['category']}** ({f['source']}) — "
                        f"conf {f['confidence']:.2f}"
                    )
                    st.caption(f"{f['message']}")

            decision = st.radio(
                "Reviewer decision",
                ["pending", "accepted", "rejected"],
                key=f"dec_{r.id}",
                horizontal=True,
                index=["pending", "accepted", "rejected"].index(dec["status"]),
            )
            notes = st.text_area("Reviewer notes", value=dec["notes"], key=f"notes_{r.id}")
            st.session_state.decisions[r.id] = {"status": decision, "notes": notes}

    st.divider()
    paper_name = "reviewed_paper"
    pdf_bytes = build_pdf_report(results, st.session_state.decisions, paper_name)
    st.markdown(download_link(pdf_bytes, "paritylens_qa_report.pdf", "📄 Download QA report (PDF)"), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Benchmark page
# -----------------------------------------------------------------------------

elif page == "Benchmark":
    st.header("Benchmark evaluation")
    st.caption("Rules-only vs semantic-only vs hybrid comparison on a 30-question labelled dataset.")

    if not BENCH_PATH.exists():
        st.error("Benchmark dataset not found.")
        st.stop()

    df = load_paper_csv(str(BENCH_PATH))

    if st.button("Run benchmark evaluation", type="primary"):
        with st.spinner("Evaluating all three configurations..."):
            comparison = compare_configs(df, semantic_threshold=threshold)

        for cfg, metrics in comparison.items():
            st.subheader(f"Configuration: {cfg}")
            o = metrics["overall"]
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Precision", o["precision"])
            c2.metric("Recall", o["recall"])
            c3.metric("F1", o["f1"])
            c4.metric("FP per 100", metrics["fp_per_100"])
            c5.metric("Latency ms/q", metrics["latency_ms"])

            per_cat = metrics["per_category"]
            chart_data = pd.DataFrame(
                {
                    "Precision": [per_cat[c]["precision"] for c in per_cat],
                    "Recall": [per_cat[c]["recall"] for c in per_cat],
                    "F1": [per_cat[c]["f1"] for c in per_cat],
                },
                index=list(per_cat.keys()),
            )
            st.bar_chart(chart_data)

# -----------------------------------------------------------------------------
# Help page
# -----------------------------------------------------------------------------

elif page == "Help":
    st.header("About ParityLens")
    st.markdown(
        """
        ParityLens is an independent QA gate for bilingual (Urdu–English) exam papers.

        **Core workflow**
        1. Upload a paired question paper (CSV in this prototype; PDF/image OCR planned).
        2. Each English question is aligned with its Urdu counterpart.
        3. Deterministic checks run on numbers, units, negation, options, formulas, named entities, and conditions.
        4. A lightweight semantic scorer flags concept-level drift.
        5. Flags enter a human reviewer queue with evidence and confidence scores.
        6. The reviewer accepts or rejects each flag.
        7. Export a QA report.

        **Mismatch taxonomy**
        - Numeric mismatch
        - Unit mismatch
        - Negation/polarity mismatch
        - Answer-option mismatch or reordering
        - Formula/symbol mismatch
        - Named-entity mismatch
        - Missing condition or constraint
        - Semantic drift

        **Prototype scope**
        This one-hour build is a hackathon demo. OCR, encryption, RBAC, and a production multilingual embedding model are explicitly left as future work.
        """
    )
