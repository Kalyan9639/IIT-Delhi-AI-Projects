from __future__ import annotations

import html
import time

import numpy as np
import pandas as pd
import streamlit as st

from src.alerts import generate_alerts
from src.config import BASE_NUMERIC_COLUMNS, CATEGORICAL_COLUMNS
from src.predict import load_model, predict_from_dataframe


REQUIRED_COLUMNS = BASE_NUMERIC_COLUMNS + CATEGORICAL_COLUMNS


def render_section_heading(title: str, subtitle: str | None = None) -> None:
    st.markdown(
        f'<div class="section-heading">{html.escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<div class="section-subheading">{html.escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def render_badge_row(items: list[str]) -> str:
    badges = "".join(
        f'<div class="pill">{html.escape(item)}</div>' for item in items if item
    )
    return f'<div class="status-pills">{badges}</div>'


def format_file_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "n/a"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(0, 229, 255, 0.18), transparent 26%),
                radial-gradient(circle at top right, rgba(0, 255, 157, 0.14), transparent 24%),
                linear-gradient(180deg, #06101c 0%, #081421 45%, #050b13 100%);
            color: #e7f4ff;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07111d 0%, #081827 100%);
            border-right: 1px solid rgba(94, 217, 255, 0.12);
        }

        section[data-testid="stSidebar"] * {
            color: #e7f4ff !important;
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            border-radius: 24px;
            padding: 1.5rem 1.7rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(100, 228, 255, 0.16);
            background: linear-gradient(135deg, rgba(7, 18, 32, 0.96), rgba(9, 31, 46, 0.86));
            box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
        }

        .hero-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(
                120deg,
                transparent 0%,
                rgba(0, 255, 194, 0.08) 48%,
                transparent 100%
            );
            transform: translateX(-110%);
            animation: sweep 6s linear infinite;
        }

        @keyframes sweep {
            0% { transform: translateX(-110%); }
            100% { transform: translateX(120%); }
        }

        .eyebrow {
            position: relative;
            z-index: 1;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-size: 0.72rem;
            font-weight: 700;
            color: #65f0ff;
        }

        .hero-title {
            position: relative;
            z-index: 1;
            margin: 0.35rem 0 0.45rem 0;
            font-size: 2.4rem;
            line-height: 1.05;
            font-weight: 800;
            color: #f4fbff;
        }

        .hero-copy {
            position: relative;
            z-index: 1;
            max-width: 900px;
            margin: 0;
            color: rgba(228, 243, 255, 0.86);
            font-size: 1rem;
            line-height: 1.65;
        }

        .scan-line {
            position: relative;
            z-index: 1;
            height: 4px;
            width: 100%;
            border-radius: 999px;
            margin-top: 1rem;
            background: linear-gradient(90deg, rgba(0, 0, 0, 0), #00e5ff, #62ffbb, rgba(0, 0, 0, 0));
            background-size: 240% 100%;
            animation: scan 2.3s linear infinite;
            opacity: 0.92;
        }

        @keyframes scan {
            0% { background-position: 0% 0; }
            100% { background-position: 240% 0; }
        }

        .status-pills {
            position: relative;
            z-index: 1;
            display: flex;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .pill {
            padding: 0.45rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(255, 255, 255, 0.05);
            color: #d8efff;
            font-size: 0.86rem;
        }

        .empty-panel {
            border-radius: 20px;
            padding: 1.2rem 1.25rem;
            border: 1px solid rgba(100, 228, 255, 0.14);
            background: rgba(4, 12, 24, 0.72);
        }

        .panel-title {
            margin: 0 0 0.6rem 0;
            font-size: 0.98rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #dff8ff;
        }

        .small-note {
            color: rgba(223, 241, 255, 0.78);
            font-size: 0.93rem;
            line-height: 1.55;
        }

        [data-testid="stMetric"] {
            background: rgba(8, 20, 36, 0.85);
            border: 1px solid rgba(100, 228, 255, 0.12);
            border-radius: 18px;
            padding: 1rem 1rem 0.85rem 1rem;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.22);
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
        }

        [data-testid="stMetricLabel"] {
            color: rgba(223, 241, 255, 0.78) !important;
        }

        [data-testid="stFileUploader"] {
            border: 1px dashed rgba(100, 228, 255, 0.35);
            border-radius: 16px;
            background: rgba(4, 12, 24, 0.58);
        }

        .stButton > button {
            border: 0;
            border-radius: 999px;
            padding: 0.65rem 1.15rem;
            font-weight: 700;
            color: #05111b;
            background: linear-gradient(135deg, #00e5ff, #00ff95);
        }

        .stButton > button:hover {
            filter: brightness(1.03);
            box-shadow: 0 0 0 1px rgba(124, 240, 255, 0.28), 0 10px 32px rgba(0, 229, 255, 0.2);
        }

        div[data-baseweb="tab-list"] {
            gap: 0.4rem;
        }

        button[data-baseweb="tab"] {
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.05) !important;
            color: #dff8ff !important;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: rgba(0, 229, 255, 0.12) !important;
            border: 1px solid rgba(100, 228, 255, 0.22) !important;
        }

        header[data-testid="stHeader"],
        #MainMenu,
        footer,
        [data-testid="stToolbar"] {
            display: none !important;
        }

        .section-heading {
            font-size: 1.38rem;
            font-weight: 850;
            letter-spacing: -0.03em;
            color: #f4fbff;
            margin: 0 0 0.35rem 0;
        }

        .section-subheading {
            margin: 0 0 1rem 0;
            color: rgba(223, 241, 255, 0.75);
            line-height: 1.6;
        }

        .hero-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.85fr);
            gap: 1rem;
            align-items: stretch;
        }

        .signal-card {
            border-radius: 22px;
            border: 1px solid rgba(100, 228, 255, 0.14);
            background: rgba(3, 12, 22, 0.78);
            padding: 1rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
        }

        .signal-label {
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #63eefb;
        }

        .signal-value {
            margin-top: 0.35rem;
            font-size: 1.5rem;
            font-weight: 850;
            color: #f4fbff;
        }

        .signal-copy {
            margin-top: 0.45rem;
            color: rgba(223, 241, 255, 0.78);
            line-height: 1.55;
            font-size: 0.95rem;
        }

        .signal-bars {
            display: grid;
            gap: 0.55rem;
            margin-top: 1rem;
        }

        .bar {
            position: relative;
            overflow: hidden;
            height: 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
        }

        .bar span {
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: linear-gradient(90deg, #00d7ff 0%, #63f3c8 100%);
            animation: sweepbar 2.8s ease-in-out infinite;
        }

        .bar:nth-child(2) span {
            animation-delay: 0.18s;
        }

        .bar:nth-child(3) span {
            animation-delay: 0.36s;
        }

        @keyframes sweepbar {
            0%, 100% {
                transform: translateX(-8%);
                filter: saturate(1);
            }
            50% {
                transform: translateX(8%);
                filter: saturate(1.2);
            }
        }

        .workflow-grid,
        .empty-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 1rem;
        }

        .workflow-card,
        .empty-card {
            border-radius: 18px;
            border: 1px solid rgba(100, 228, 255, 0.12);
            background: rgba(4, 14, 24, 0.76);
            padding: 1rem;
        }

        .workflow-index {
            width: 2rem;
            height: 2rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #00e5ff 0%, #7ef7b7 100%);
            color: #03101a;
            font-size: 0.86rem;
            font-weight: 850;
            margin-bottom: 0.75rem;
        }

        .workflow-title,
        .empty-card-title {
            color: #f4fbff;
            font-weight: 850;
            margin-bottom: 0.3rem;
        }

        .workflow-copy,
        .empty-card-copy {
            color: rgba(223, 241, 255, 0.75);
            line-height: 1.55;
            font-size: 0.93rem;
        }

        .panel {
            border-radius: 22px;
            border: 1px solid rgba(100, 228, 255, 0.12);
            background: rgba(4, 14, 24, 0.78);
            padding: 1rem 1.05rem;
        }

        .panel + .panel {
            margin-top: 0.85rem;
        }

        .panel-title {
            margin: 0 0 0.65rem 0;
            font-size: 0.76rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #63eefb;
        }

        .panel-copy {
            color: rgba(223, 241, 255, 0.78);
            line-height: 1.6;
            font-size: 0.94rem;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        .chip {
            padding: 0.38rem 0.7rem;
            border-radius: 999px;
            border: 1px solid rgba(100, 228, 255, 0.14);
            background: rgba(255, 255, 255, 0.04);
            color: #e9f8ff;
            font-size: 0.82rem;
        }

        .results-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.38fr) minmax(320px, 0.82fr);
            gap: 0.9rem;
        }

        .chart-panel,
        .table-panel {
            border-radius: 22px;
            border: 1px solid rgba(100, 228, 255, 0.12);
            background: rgba(4, 14, 24, 0.78);
            padding: 1rem;
        }

        .table-panel {
            height: 100%;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(8, 20, 36, 0.95), rgba(4, 13, 22, 0.9));
            border: 1px solid rgba(100, 228, 255, 0.12);
            border-radius: 18px;
            padding: 0.95rem 1rem 0.85rem 1rem;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.22);
        }

        [data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-size: 1.7rem;
            line-height: 1.15;
        }

        [data-testid="stMetricLabel"] {
            color: rgba(223, 241, 255, 0.78) !important;
        }

        [data-testid="stFileUploader"] {
            border: 1px dashed rgba(100, 228, 255, 0.38);
            border-radius: 18px;
            background: rgba(4, 12, 24, 0.58);
        }

        .stButton > button {
            border: 0;
            border-radius: 999px;
            padding: 0.72rem 1.15rem;
            font-weight: 800;
            color: #04111b;
            background: linear-gradient(135deg, #00e5ff 0%, #00ff95 100%);
        }

        .stButton > button:hover {
            filter: brightness(1.04);
            box-shadow: 0 0 0 1px rgba(124, 240, 255, 0.26), 0 14px 32px rgba(0, 229, 255, 0.18);
        }

        .empty-state {
            margin-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-grid">
                <div>
                    <div class="eyebrow">Security Operations Console</div>
                    <div class="hero-title">AI Cybersecurity Threat Detection</div>
                    <p class="hero-copy">
                        Upload UNSW-NB15-style traffic data, trigger a live threat scan, and review
                        suspicious flows with confidence scores and generated alerts in a clean,
                        command-center style interface.
                    </p>
                    {render_badge_row([
                        f"{len(REQUIRED_COLUMNS)} required feature columns",
                        "ExtraTrees threat model",
                        "Live scan and alert workflow",
                    ])}
                </div>
                <div class="signal-card">
                    <div class="signal-label">Live posture</div>
                    <div class="signal-value">Ready to scan</div>
                    <div class="signal-copy">
                        Drop a CSV to validate the schema and start threat scoring.
                    </div>
                    <div class="signal-bars">
                        <div class="bar"><span></span></div>
                        <div class="bar"><span></span></div>
                        <div class="bar"><span></span></div>
                    </div>
                </div>
            </div>
            <div class="workflow-grid">
                <div class="workflow-card">
                    <div class="workflow-index">1</div>
                    <div class="workflow-title">Ingest</div>
                    <div class="workflow-copy">
                        Upload a UNSW-NB15 CSV with the required network flow features.
                    </div>
                </div>
                <div class="workflow-card">
                    <div class="workflow-index">2</div>
                    <div class="workflow-title">Score</div>
                    <div class="workflow-copy">
                        Run the threat scan while the model validates and predicts each row.
                    </div>
                </div>
                <div class="workflow-card">
                    <div class="workflow-index">3</div>
                    <div class="workflow-title">Respond</div>
                    <div class="workflow-copy">
                        Review alerts, confidence levels, and export the scored dataset.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Mission Control</div>
            <div class="panel-copy">
                This dashboard scores UNSW-NB15 network flows and highlights suspicious
                traffic with a calm, high-contrast security interface.
            </div>
        </div>
        <div class="panel">
            <div class="panel-title">Scan Flow</div>
            <div class="chip-row">
                <div class="chip">1. Upload CSV</div>
                <div class="chip">2. Run scan</div>
                <div class="chip">3. Review alerts</div>
            </div>
        </div>
        <div class="panel">
            <div class="panel-title">Input Requirements</div>
            <div class="panel-copy">
                {len(REQUIRED_COLUMNS)} required columns, including the categorical features
                <strong>proto</strong>, <strong>service</strong>, and <strong>state</strong>.
            </div>
            <div class="chip-row" style="margin-top: 0.75rem;">
                <div class="chip">id optional</div>
                <div class="chip">label optional</div>
                <div class="chip">attack_cat optional</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="panel empty-state">
            <div class="panel-title">Awaiting packet capture</div>
            <div class="panel-copy">
                Upload a CSV to activate the scanner. The page will switch into a refined
                security dashboard with progress updates, a threat summary, scored traffic,
                and exportable alerts.
            </div>
            <div class="empty-grid">
                <div class="empty-card">
                    <div class="empty-card-title">Ingest</div>
                    <div class="empty-card-copy">Load UNSW-NB15-style network flow rows.</div>
                </div>
                <div class="empty-card">
                    <div class="empty-card-title">Inspect</div>
                    <div class="empty-card-copy">Preview the file and validate the schema.</div>
                </div>
                <div class="empty-card">
                    <div class="empty-card-title">Respond</div>
                    <div class="empty-card-copy">Score threats and review alerts instantly.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_cached_model():
    if "_cached_model" not in st.session_state:
        st.session_state["_cached_model"] = load_model()
    return st.session_state["_cached_model"]


def missing_required_columns(df: pd.DataFrame) -> list[str]:
    return [column for column in REQUIRED_COLUMNS if column not in df.columns]


def run_detection(df: pd.DataFrame):
    progress = st.progress(0, text="Preparing security scan")
    log = st.empty()

    log.info("Loading the trained model artifact.")
    progress.progress(15, text="Loading model")
    time.sleep(0.08)
    model = get_cached_model()

    log.info("Checking required UNSW-NB15 input columns.")
    progress.progress(35, text="Validating input schema")
    time.sleep(0.08)
    missing = missing_required_columns(df)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    log.info("Running inference on uploaded traffic rows.")
    progress.progress(65, text="Running inference")
    time.sleep(0.08)
    predictions, probabilities = predict_from_dataframe(df, model=model, return_proba=True)

    log.info("Generating alerts and severity metadata.")
    progress.progress(85, text="Generating alerts")
    time.sleep(0.08)
    alerts = generate_alerts(df, predictions, probabilities, include_normal=False)

    progress.progress(100, text="Security scan complete")
    log.success("Threat scan complete.")
    return np.asarray(predictions), np.asarray(probabilities), alerts


def render_results(df: pd.DataFrame, predictions: np.ndarray, probabilities: np.ndarray, alerts) -> None:
    threat_scores = probabilities[:, 1] if probabilities.ndim == 2 else probabilities

    scored = df.copy()
    scored["Prediction"] = predictions.astype(int)
    scored["Threat Score"] = threat_scores

    threat_count = int(predictions.sum())
    normal_count = int(len(predictions) - threat_count)
    threat_ratio = (threat_count / len(predictions)) if len(predictions) else 0.0
    max_confidence = float(threat_scores.max()) if len(threat_scores) else 0.0
    avg_confidence = float(threat_scores.mean()) if len(threat_scores) else 0.0
    severity_order = ["critical", "high", "medium", "low"]
    severity_counts = (
        pd.Series([alert.get("severity", "unknown") for alert in alerts]).value_counts()
        if alerts
        else pd.Series(dtype=int)
    ).reindex(severity_order, fill_value=0)

    render_section_heading(
        "Threat Summary",
        "A compact readout of what the model saw, how strongly it reacted, and where the highest-risk rows are clustered.",
    )

    if threat_count:
        st.warning(f"{threat_count} row(s) were flagged as potential threats.")
    else:
        st.success("No threats were detected in the uploaded sample.")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("Rows Scored", f"{len(scored):,}")
    metric_2.metric("Threats Detected", f"{threat_count:,}")
    metric_3.metric("Threat Rate", f"{threat_ratio:.0%}")
    metric_4.metric("Peak Score", f"{max_confidence:.3f}")

    st.markdown(
        render_badge_row(
            [
                f"Normal rows: {normal_count}",
                f"Threat rows: {threat_count}",
                f"Average score: {avg_confidence:.3f}",
                f"Peak score: {max_confidence:.3f}",
            ]
        ),
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Overview", "Scored Data", "Alerts"])

    with tabs[0]:
        left, right = st.columns([1.15, 0.85], gap="large")

        with left:
            with st.container(border=True):
                st.markdown(
                    '<div class="panel-title">Traffic profile</div>',
                    unsafe_allow_html=True,
                )
                st.bar_chart(pd.Series({"Normal": normal_count, "Threat": threat_count}))

                trend = scored.reset_index().rename(columns={"index": "Row"})[["Row", "Threat Score"]]
                trend = trend.head(120).set_index("Row")
                st.markdown(
                    '<div class="panel-title" style="margin-top: 1rem;">Confidence trend</div>',
                    unsafe_allow_html=True,
                )
                st.line_chart(trend)

        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="panel-title">Top risk rows</div>',
                    unsafe_allow_html=True,
                )
                top_risks = scored.sort_values("Threat Score", ascending=False).head(10).copy()
                display_columns = [
                    column
                    for column in ["id", "proto", "service", "state", "Threat Score", "Prediction"]
                    if column in top_risks.columns
                ]
                if display_columns:
                    st.dataframe(
                        top_risks[display_columns],
                        use_container_width=True,
                        hide_index=True,
                        height=310,
                        column_config={
                            "Threat Score": st.column_config.NumberColumn("Threat Score", format="%.3f"),
                        },
                    )
                else:
                    st.dataframe(
                        top_risks.head(10),
                        use_container_width=True,
                        hide_index=True,
                        height=310,
                    )

                st.markdown(
                    '<div class="panel-title" style="margin-top: 1rem;">Severity breakdown</div>',
                    unsafe_allow_html=True,
                )
                if severity_counts.sum():
                    st.bar_chart(severity_counts)
                else:
                    st.info("No alerts were generated, so there is no severity breakdown to show.")

    with tabs[1]:
        with st.container(border=True):
            st.dataframe(
                scored.head(100),
                use_container_width=True,
                height=440,
                hide_index=True,
                column_config={
                    "Threat Score": st.column_config.NumberColumn("Threat Score", format="%.3f"),
                    "Prediction": st.column_config.NumberColumn("Prediction", format="%d"),
                },
            )

        st.download_button(
            "Download scored CSV",
            scored.to_csv(index=False).encode("utf-8"),
            file_name="threat_scored_output.csv",
            mime="text/csv",
            use_container_width=False,
        )

    with tabs[2]:
        if alerts:
            alert_df = pd.DataFrame(alerts)
            with st.container(border=True):
                st.dataframe(
                    alert_df,
                    use_container_width=True,
                    height=340,
                    hide_index=True,
                    column_config={
                        "confidence": st.column_config.NumberColumn("confidence", format="%.3f"),
                    },
                )
        else:
            st.info("No alerts were generated for this file.")


def main() -> None:
    st.set_page_config(
        page_title="AI Cybersecurity Threat Detection",
        page_icon="S",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_theme()
    render_hero()

    with st.sidebar:
        render_sidebar()

    render_section_heading(
        "Upload traffic data",
        "Drop an UNSW-NB15 CSV to validate the schema and start threat scoring.",
    )
    uploaded_file = st.file_uploader(
        "Upload Network Data CSV",
        type=["csv"],
        label_visibility="collapsed",
        help="CSV file with UNSW-NB15-style traffic features.",
    )

    if not uploaded_file:
        render_empty_state()
        return

    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"Could not read the uploaded file: {exc}")
        return

    missing = missing_required_columns(df)
    if missing:
        st.markdown(
            f"""
            <div class="panel">
                <div class="panel-title">Schema check failed</div>
                <div class="panel-copy">
                    Missing required UNSW-NB15 columns: {html.escape(", ".join(missing))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.error("The uploaded file does not include all required columns.")
        return

    file_size = format_file_size(getattr(uploaded_file, "size", None))
    summary_cols = st.columns(4)
    summary_cols[0].metric("Rows", f"{len(df):,}")
    summary_cols[1].metric("Columns", f"{df.shape[1]:,}")
    summary_cols[2].metric("Required fields present", f"{len(REQUIRED_COLUMNS) - len(missing):,}")
    summary_cols[3].metric("File size", file_size)

    st.markdown(
        render_badge_row(
            [
                f"Loaded file: {html.escape(uploaded_file.name)}",
                "Schema: ready",
                "Model: ExtraTrees",
            ]
        ),
        unsafe_allow_html=True,
    )

    render_section_heading(
        "Uploaded traffic preview",
        "Inspect the first 20 rows before you launch the live scan.",
    )
    st.dataframe(
        df.head(20),
        use_container_width=True,
        height=320,
        hide_index=True,
    )

    control_left, control_right = st.columns([1.15, 0.55], gap="large")
    with control_left:
        st.markdown(
            """
            <div class="panel">
                <div class="panel-title">Scan mode</div>
                <div class="panel-copy">
                    The model will load, validate the schema, score each row, and then generate
                    alerts and confidence metadata.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with control_right:
        run_clicked = st.button("Run Threat Scan", type="primary", use_container_width=True)

    if not run_clicked:
        st.info("Click Run Threat Scan to start scoring this upload.")
        return

    try:
        with st.status("Security engine processing", expanded=True) as status:
            status.write("Loading the trained model.")
            status.write("Validating the traffic schema.")
            status.write("Running the prediction pipeline.")
            status.write("Generating alert metadata.")
            predictions, probabilities, alerts = run_detection(df)
            status.update(label="Threat scan complete", state="complete", expanded=False)
    except FileNotFoundError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(f"Unable to score the uploaded file: {exc}")
        return

    render_results(df, predictions, probabilities, alerts)


if __name__ == "__main__":
    main()
