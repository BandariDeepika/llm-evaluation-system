import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
project_root_string = str(PROJECT_ROOT)
if project_root_string in sys.path:
    sys.path.remove(project_root_string)
sys.path.insert(0, project_root_string)

import streamlit as st
import pandas as pd
import requests

from frontend.api_config import (
    DEFAULT_API_TIMEOUT_SECONDS,
    get_api_base_url,
    get_api_timeout,
)
from frontend.chart_data import (
    batch_chart_data,
    hallucination_status,
    single_score_data,
)
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AegisEval",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    :root {
        color-scheme: dark;
        --aegis-bg: #080c19;
        --aegis-surface: #11182a;
        --aegis-surface-raised: #151e33;
        --aegis-border: rgba(148, 163, 184, 0.16);
        --aegis-muted: #9aa8c2;
        --aegis-cyan: #45d5e7;
        --aegis-violet: #8a72ff;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 82% 0%, rgba(72, 72, 182, 0.18), transparent 36%),
            radial-gradient(ellipse at 0% 36%, rgba(24, 135, 163, 0.09), transparent 32%),
            var(--aegis-bg);
        color: #edf3ff;
    }

    [data-testid="stMain"] .block-container {
        max-width: 1440px;
        padding: 2.35rem 3rem 4rem;
    }

    [data-testid="stHeader"] {
        background: rgba(8, 12, 25, 0.96);
    }

    [data-testid="stToolbar"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(9, 14, 29, 0.96);
        border-right: 1px solid var(--aegis-border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.6rem;
    }

    [data-testid="stSidebar"] h1 {
        font-size: 1.45rem;
        letter-spacing: -0.04em;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 9px;
        padding: 0.28rem 0.55rem;
        transition: background-color 140ms ease, color 140ms ease;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(69, 213, 231, 0.08);
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(100deg, rgba(69, 213, 231, 0.14), rgba(138, 114, 255, 0.12));
        color: #f3fbff;
    }

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: var(--aegis-muted);
    }

    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label {
        color: #d6e0f2;
    }

    [data-testid="stRadio"] label p {
        color: #c7d3e8;
    }

    [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
        background: #0d1425 !important;
        border-color: #8291ad !important;
    }

    [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child {
        background: #0d1425 !important;
        border-color: var(--aegis-cyan) !important;
    }

    [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div:first-child {
        background: var(--aegis-cyan) !important;
    }

    [data-testid="stRadio"] input[type="radio"] {
        appearance: none;
        display: grid;
        width: 1rem;
        height: 1rem;
        margin-top: 0.15rem;
        border: 2px solid #8291ad;
        border-radius: 50%;
        background: #0d1425;
        place-content: center;
    }

    [data-testid="stRadio"] input[type="radio"]::before {
        width: 0.42rem;
        height: 0.42rem;
        border-radius: 50%;
        background: var(--aegis-cyan);
        content: "";
        transform: scale(0);
        transition: transform 120ms ease;
    }

    [data-testid="stRadio"] input[type="radio"]:checked {
        border-color: var(--aegis-cyan);
    }

    [data-testid="stRadio"] input[type="radio"]:checked::before {
        transform: scale(1);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(21, 30, 51, 0.96), rgba(15, 23, 41, 0.92));
        border: 1px solid var(--aegis-border);
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
        transition: border-color 160ms ease, transform 160ms ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(69, 213, 231, 0.36);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] p,
    [data-testid="stCaptionContainer"] p {
        color: var(--aegis-muted);
    }

    [data-testid="stMetricValue"] {
        color: #f4f7ff;
        font-weight: 650;
    }

    .main-title {
        font-size: clamp(2rem, 4vw, 2.75rem);
        font-weight: 700;
        margin: 0 0 0.35rem;
        letter-spacing: -0.03em;
        background: linear-gradient(100deg, #f5f7ff 20%, #73ddeb 66%, #a69aff);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .sub-title {
        color: var(--aegis-muted);
        font-size: 1rem;
        margin-bottom: 1.7rem;
    }

    h1, h2, h3 {
        letter-spacing: -0.025em;
    }

    h2, h3 {
        color: #e8efff;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div,
    [data-testid="stFileUploader"] section {
        background: rgba(13, 20, 37, 0.82);
        border-color: rgba(148, 163, 184, 0.22);
        border-radius: 10px;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        background-color: rgba(13, 20, 37, 0.96) !important;
        color: #f2f6ff !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
    }

    [data-testid="stTextInput"] button {
        background-color: #18243b !important;
        color: #dce7fb !important;
    }

    [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stTextInput"] [data-baseweb="base-input"] {
        background-color: rgba(13, 20, 37, 0.96) !important;
        border-color: rgba(148, 163, 184, 0.28) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--aegis-cyan);
        box-shadow: 0 0 0 1px rgba(69, 213, 231, 0.42);
    }

    [data-testid="stForm"] {
        background: linear-gradient(145deg, rgba(18, 26, 45, 0.88), rgba(12, 18, 33, 0.84));
        border: 1px solid var(--aegis-border);
        border-radius: 16px;
        padding: 1.35rem 1.5rem;
    }

    [data-testid="stButton"] button,
    [data-testid="stFormSubmitButton"] button,
    [data-testid="stDownloadButton"] button {
        border-radius: 10px;
        font-weight: 600;
        transition: transform 140ms ease, border-color 140ms ease, filter 140ms ease;
    }

    [data-testid="stButton"] button:hover,
    [data-testid="stFormSubmitButton"] button:hover,
    [data-testid="stDownloadButton"] button:hover {
        border-color: rgba(69, 213, 231, 0.62);
        transform: translateY(-1px);
    }

    [data-testid="stButton"] button[kind="primary"],
    [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
        background: linear-gradient(105deg, #168eaa, #5b66d8 72%, #765ce1);
        border: 0;
        color: white;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border: 1px solid var(--aegis-border);
        border-radius: 12px;
        overflow: hidden;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    @media (max-width: 800px) {
        [data-testid="stMain"] .block-container {
            padding: 1.5rem 1rem 3rem;
        }

        [data-testid="stForm"] {
            padding: 1rem;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# API CONFIGURATION
# ============================================================

API_BASE_URL = get_api_base_url(st.secrets, os.environ)
API_TIMEOUT_SECONDS = get_api_timeout(st.secrets, os.environ, DEFAULT_API_TIMEOUT_SECONDS)
API_TIMEOUT = (10, API_TIMEOUT_SECONDS)
API_URL = f"{API_BASE_URL}/evaluate"
AUTH_URL = f"{API_BASE_URL}/auth"


def api_request_error(error, action="request"):
    if isinstance(error, requests.Timeout):
        return (
            f"The API did not respond within {API_TIMEOUT_SECONDS:g} seconds while "
            f"trying to {action}. Render may be waking the service; please retry. "
            "If this continues, check the Render service logs."
        )
    if isinstance(error, requests.ConnectionError):
        return (
            f"Could not connect to the API at {API_BASE_URL}. Verify the "
            "API_BASE_URL Streamlit secret matches the running Render service."
        )
    return f"API {action} failed: {error}"


def api_response_error(response, action):
    try:
        detail = response.json().get("detail")
    except (ValueError, AttributeError):
        detail = None
    if not detail:
        detail = "The server returned an unexpected response."
    return f"Unable to {action} (HTTP {response.status_code}): {detail}"


# ============================================================
# SESSION STATE
# ============================================================

if "batch_results" not in st.session_state:
    st.session_state.batch_results = None

if "single_result" not in st.session_state:
    st.session_state.single_result = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

if "auth_mode_version" not in st.session_state:
    st.session_state.auth_mode_version = 0


def auth_headers():
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def update_auth_mode(widget_key):
    st.session_state.auth_mode = st.session_state[widget_key]


def show_auth_page():
    left, center, right = st.columns([1.15, 1.7, 1.15])
    with center:
        st.markdown(
            '<div style="text-align:center; padding:1.2rem 0 0.8rem;">'
            '<div style="display:inline-block; padding:0.32rem 0.8rem; margin-bottom:0.9rem; '
            'border:1px solid rgba(69,213,231,.32); border-radius:999px; '
            'background:rgba(69,213,231,.08); color:#72dce9; font-size:.76rem; '
            'font-weight:700; letter-spacing:.12em; text-transform:uppercase;">'
            'AI Response Evaluation</div>'
            '<div class="main-title">AegisEval</div>'
            '<div class="sub-title">Sign in to evaluate responses and review your private history.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        auth_notice = st.session_state.pop("auth_notice", None)
        if auth_notice:
            st.success(auth_notice)
        mode_widget_key = f"auth_mode_{st.session_state.auth_mode_version}"
        mode = st.radio(
            "Account",
            ["Login", "Register"],
            horizontal=True,
            index=0 if st.session_state.auth_mode == "Login" else 1,
            key=mode_widget_key,
            on_change=update_auth_mode,
            args=(mode_widget_key,),
        )

        with st.form(f"{mode.lower()}_form"):
            if mode == "Register":
                full_name = st.text_input("Full name")
                email = st.text_input("Email")
                username = st.text_input("Username")
            else:
                username = st.text_input("Username or email")
            password = st.text_input("Password", type="password")
            confirm_password = (
                st.text_input("Confirm password", type="password")
                if mode == "Register"
                else None
            )
            submitted = st.form_submit_button(mode, type="primary", use_container_width=True)

        if not submitted:
            return
        if mode == "Register" and password != confirm_password:
            st.error("Passwords do not match.")
            return

        endpoint = "register" if mode == "Register" else "login"
        payload = (
            {
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password,
                "confirm_password": confirm_password,
            }
            if mode == "Register"
            else {"username_or_email": username, "password": password}
        )
        try:
            response = requests.post(
                f"{AUTH_URL}/{endpoint}",
                json=payload,
                timeout=API_TIMEOUT,
            )
            if response.ok:
                result = response.json()
                if mode == "Register":
                    st.session_state.pop("auth_token", None)
                    st.session_state.pop("auth_user", None)
                    st.session_state.auth_mode = "Login"
                    st.session_state.auth_mode_version += 1
                    st.session_state.auth_notice = (
                        "Registration successful. Please log in with your new credentials."
                    )
                else:
                    st.session_state.auth_token = result["token"]
                    st.session_state.auth_user = result["user"]
                st.rerun()
            try:
                detail = response.json().get("detail", "Unable to authenticate.")
            except (ValueError, AttributeError):
                detail = "Unable to authenticate. Check the backend connection."
            st.error(str(detail))
        except requests.RequestException as error:
            st.error(api_request_error(error, "authenticate"))


def clear_auth_state():
    for key in ("auth_token", "auth_user", "batch_results", "single_result"):
        st.session_state.pop(key, None)
    st.session_state.auth_mode = "Login"
    st.session_state.auth_mode_version += 1


def render_account_dashboard():
    try:
        dashboard_response = requests.get(
            f"{AUTH_URL}/dashboard",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        dashboard_response.raise_for_status()
        summary = dashboard_response.json()
        evaluations = summary.get("evaluations", [])
    except requests.RequestException as error:
        st.error(api_request_error(error, "load your account dashboard"))
        return
    except ValueError as error:
        st.error(f"The API returned invalid dashboard data: {error}")
        return

    st.subheader("Your evaluation activity")
    columns = st.columns(4)
    columns[0].metric("Total evaluations", summary["total_evaluations"])
    columns[1].metric("PASS", summary["pass_count"])
    columns[2].metric("NEEDS IMPROVEMENT", summary["needs_improvement_count"])
    columns[3].metric("FAIL", summary["fail_count"])

    score_values = {
        "Relevance": [],
        "Accuracy": [],
        "Completeness": [],
        "Hallucination": [],
    }
    hallucination_outcomes = {
        "Detected": 0,
        "Not detected": 0,
        "Uncertain": 0,
    }
    for item in evaluations:
        try:
            metrics = json.loads(item.get("metrics_json") or "{}").get("metrics", {})
        except (TypeError, json.JSONDecodeError):
            continue
        metric_keys = {
            "Relevance": ("relevance",),
            "Accuracy": ("factuality", "accuracy"),
            "Completeness": ("completeness",),
            "Hallucination": ("hallucination",),
        }
        for label, possible_keys in metric_keys.items():
            metric = next(
                (metrics[key] for key in possible_keys if key in metrics),
                None,
            )
            score = metric.get("score") if isinstance(metric, dict) else None
            if score is None:
                continue
            try:
                score_values[label].append(float(score))
            except (TypeError, ValueError):
                continue
        hallucination = metrics.get("hallucination", {})
        if isinstance(hallucination, dict):
            if hallucination.get("certainty") == "uncertain" or hallucination.get("hallucination_detected") is None:
                hallucination_outcomes["Uncertain"] += 1
            elif hallucination["hallucination_detected"]:
                hallucination_outcomes["Detected"] += 1
            else:
                hallucination_outcomes["Not detected"] += 1

    chart_data = {
        label: sum(values) / len(values)
        for label, values in score_values.items()
        if values
    }
    if chart_data:
        st.subheader("Average evaluation scores")
        st.caption("Accuracy uses the evaluation engine's factuality score. Metrics without numeric scores are omitted.")
        chart = pd.DataFrame(
            {"Score": chart_data.values()},
            index=chart_data.keys(),
        )
        st.bar_chart(chart, y="Score")
    else:
        st.info("Score charts will appear after your evaluations produce numeric metric scores.")

    if any(hallucination_outcomes.values()):
        st.subheader("Hallucination outcomes")
        st.caption("Counts reflect the evaluator's detected, not detected, or uncertain classifications.")
        st.bar_chart(
            pd.DataFrame(
                {"Evaluations": hallucination_outcomes.values()},
                index=hallucination_outcomes.keys(),
            ),
            y="Evaluations",
        )

    st.markdown("---")


def render_single_result_charts(result):
    score_data = single_score_data(result)
    st.subheader("Evaluation score comparison")
    if score_data.empty:
        st.info("No numeric evaluation scores were returned for this response.")
    else:
        st.bar_chart(score_data, y="Score", y_label="Score (0-10)", height=320)

    if "Hallucination" not in score_data.index:
        status = hallucination_status(result)
        if status:
            st.metric("Hallucination classification", status)
        st.caption(
            "The current hallucination evaluator returns a classification, not a numeric score; "
            "no hallucination score is inferred."
        )


def render_batch_result_charts(results):
    response_scores, verdict_counts, average_scores = batch_chart_data(results)
    st.markdown("---")
    st.subheader("Batch score comparison")
    if response_scores.empty:
        st.info("No numeric scores are available to chart for this batch.")
    else:
        st.bar_chart(
            response_scores,
            x="Response",
            y=list(response_scores.columns[1:]),
            y_label="Score (0-10)",
            height=380,
        )
        st.caption("Each bar uses a numeric score returned by the evaluator; missing scores are omitted.")
    if (
        "Hallucination" in results.columns
        and "Hallucination" not in response_scores.columns
        and "Hallucination Score" not in response_scores.columns
    ):
        st.caption(
            "Hallucination is returned as a classification for this batch, not a numeric score, "
            "so it is not converted into a score."
        )

    st.subheader("Verdict counts")
    st.bar_chart(verdict_counts, x="Verdict", y="Count", y_label="Responses", height=260)

    if average_scores.empty:
        st.info("Average score summary is unavailable because no numeric scores were returned.")
    else:
        st.subheader("Average evaluation scores")
        st.bar_chart(
            average_scores,
            y="Average Score",
            y_label="Average score (0-10)",
            height=300,
        )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_average(df, column):

    if column not in df.columns:
        return None

    values = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if values.empty:
        return None

    return float(values.mean())


def get_value(data, names, default=None):

    if not isinstance(data, dict):
        return default

    for name in names:

        if name in data:
            return data[name]

    return default


def normalize_score(value):

    if isinstance(value, dict):

        return value.get(
            "score",
            value.get("value", None)
        )

    return value


def clean_verdict(value):

    if value is None:
        return "UNKNOWN"

    text = str(value).strip().upper()

    if text == "PASS":
        return "PASS"

    if text in [
        "NEEDS IMPROVEMENT",
        "NEEDS_IMPROVEMENT",
        "NEEDS-IMPROVEMENT",
    ]:
        return "NEEDS IMPROVEMENT"

    if text == "FAIL":
        return "FAIL"

    if text == "ERROR":
        return "ERROR"

    return text


def format_score(value):

    if value is None:
        return "N/A"

    try:

        if pd.isna(value):
            return "N/A"

    except Exception:
        pass

    try:
        return f"{float(value):.2f}"

    except Exception:
        return str(value)


def extract_nested_score(data, key):

    value = data.get(key)

    if isinstance(value, dict):
        return value.get("score")

    return value


def extract_hallucination_status(data):

    hallucination = data.get(
        "hallucination",
        {}
    )

    if not isinstance(hallucination, dict):
        return "N/A"

    certainty = str(
        hallucination.get(
            "certainty",
            ""
        )
    ).lower()

    detected = hallucination.get(
        "hallucination_detected"
    )

    unsupported = hallucination.get(
        "unsupported_claims",
        []
    )

    if certainty == "uncertain":
        return "Uncertain"

    if detected is True:
        return "Detected"

    if detected is False:
        return "Not Detected"

    if isinstance(unsupported, list) and unsupported:
        return "Detected"

    return "N/A"


# ============================================================
# M4.2 - PDF HELPER FUNCTIONS
# ============================================================

def pdf_clean_text(value):

    if value is None:
        return ""

    if isinstance(value, float):

        try:

            if pd.isna(value):
                return ""

        except Exception:
            pass

    if isinstance(value, list):

        return ", ".join(
            str(item)
            for item in value
        )

    if isinstance(value, dict):

        return str(value)

    return str(value)


def pdf_escape(value):

    return escape(
        pdf_clean_text(value)
    )


def pdf_score(value):

    if value is None:
        return "N/A"

    try:

        if pd.isna(value):
            return "N/A"

    except Exception:
        pass

    try:

        return f"{float(value):.2f}"

    except Exception:

        text = pdf_clean_text(value)

        if not text:
            return "N/A"

        return text


def create_batch_pdf(results_df):

    """
    M4.2 PDF Batch Summary

    Generates a professional PDF containing:

    1. Batch summary
    2. Verdict distribution
    3. Average evaluation scores
    4. Hallucination analysis
    5. Completeness analysis
    6. Individual evaluation results
    7. Evaluation reasoning
    8. Verdict reasoning
    9. Unsupported claims
    10. Missing / partial aspects
    11. Recommendations
    """

    if results_df is None:
        raise ValueError(
            "No batch evaluation results available."
        )

    if results_df.empty:
        raise ValueError(
            "Batch evaluation results are empty."
        )

    df = results_df.copy()

    buffer = BytesIO()

    # --------------------------------------------------------
    # PDF DOCUMENT
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=40,
        bottomMargin=40,
        title="LLM Batch Evaluation Summary",
        author=(
            "Automated LLM Evaluation and "
            "Hallucination Detection System"
        ),
    )

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "PDFSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "PDFHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
    )

    subheading_style = ParagraphStyle(
        "PDFSubHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        spaceBefore=8,
        spaceAfter=5,
    )

    normal_style = ParagraphStyle(
        "PDFNormal",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        spaceAfter=6,
    )

    small_style = ParagraphStyle(
        "PDFSmall",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        spaceAfter=4,
    )

    # --------------------------------------------------------
    # STORY
    # --------------------------------------------------------

    story = []

    # --------------------------------------------------------
    # BASIC COUNTS
    # --------------------------------------------------------

    total = len(df)

    if "Verdict" in df.columns:

        verdict_series = (
            df["Verdict"]
            .astype(str)
            .apply(clean_verdict)
        )

    else:

        verdict_series = pd.Series(
            ["UNKNOWN"] * total
        )

    pass_count = int(
        (verdict_series == "PASS").sum()
    )

    needs_count = int(
        (
            verdict_series
            == "NEEDS IMPROVEMENT"
        ).sum()
    )

    fail_count = int(
        (verdict_series == "FAIL").sum()
    )

    error_count = int(
        (verdict_series == "ERROR").sum()
    )

    pass_percentage = (
        pass_count / total * 100
        if total
        else 0
    )

    needs_percentage = (
        needs_count / total * 100
        if total
        else 0
    )

    fail_percentage = (
        fail_count / total * 100
        if total
        else 0
    )

    # --------------------------------------------------------
    # AVERAGE SCORES
    # --------------------------------------------------------

    avg_relevance = safe_average(
        df,
        "Relevance"
    )

    avg_factuality = safe_average(
        df,
        "Factuality"
    )

    avg_faithfulness = safe_average(
        df,
        "Faithfulness"
    )

    avg_completeness = safe_average(
        df,
        "Completeness"
    )

    avg_semantic_similarity = safe_average(
        df,
        "Semantic Similarity"
    )

    avg_overall_score = safe_average(
        df,
        "Overall Score"
    )

    avg_weighted_score = safe_average(
        df,
        "Weighted Score"
    )

    # --------------------------------------------------------
    # HALLUCINATION ANALYSIS
    # --------------------------------------------------------

    hallucination_count = 0
    uncertain_hallucination_count = 0
    not_detected_count = 0
    unsupported_claim_count = 0

    if "Hallucination" in df.columns:

        for value in df["Hallucination"]:

            status = str(
                value
            ).strip().lower()

            if status == "detected":

                hallucination_count += 1

            elif status == "uncertain":

                uncertain_hallucination_count += 1

            elif status == "not detected":

                not_detected_count += 1

    # Count unsupported claims from Full Report
    if "Full Report" in df.columns:

        for report in df["Full Report"]:

            if isinstance(report, dict):

                hallucination_data = report.get(
                    "hallucination",
                    {}
                )

                if isinstance(
                    hallucination_data,
                    dict
                ):

                    claims = hallucination_data.get(
                        "unsupported_claims",
                        []
                    )

                    if isinstance(claims, list):

                        unsupported_claim_count += len(
                            claims
                        )

    # --------------------------------------------------------
    # COMPLETENESS ANALYSIS
    # --------------------------------------------------------

    missing_aspects_count = 0
    partial_aspects_count = 0

    if "Full Report" in df.columns:

        for report in df["Full Report"]:

            if isinstance(report, dict):

                completeness_data = report.get(
                    "completeness",
                    {}
                )

                if isinstance(
                    completeness_data,
                    dict
                ):

                    details = completeness_data.get(
                        "details",
                        {}
                    )

                    if isinstance(
                        details,
                        dict
                    ):

                        missing = details.get(
                            "missing_aspects",
                            []
                        )

                        partial = details.get(
                            "partial_aspects",
                            []
                        )

                        if isinstance(
                            missing,
                            list
                        ):

                            missing_aspects_count += len(
                                missing
                            )

                        if isinstance(
                            partial,
                            list
                        ):

                            partial_aspects_count += len(
                                partial
                            )

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "Automated LLM Evaluation and "
            "Hallucination Detection System",
            title_style
        )
    )

    story.append(
        Paragraph(
            "M4.2 - Batch Evaluation Summary Report",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            "This report summarizes the automated "
            "evaluation of multiple AI-generated responses.",
            normal_style
        )
    )

    story.append(
        Spacer(1, 8)
    )

    # ========================================================
    # 1. BATCH SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "1. Batch Evaluation Summary",
            heading_style
        )
    )

    summary_data = [
        ["Metric", "Value"],
        [
            "Total Responses",
            str(total)
        ],
        [
            "PASS",
            f"{pass_count} ({pass_percentage:.1f}%)"
        ],
        [
            "NEEDS IMPROVEMENT",
            f"{needs_count} "
            f"({needs_percentage:.1f}%)"
        ],
        [
            "FAIL",
            f"{fail_count} ({fail_percentage:.1f}%)"
        ],
        [
            "ERROR",
            str(error_count)
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[280, 170]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#222222")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    story.append(summary_table)

    story.append(
        Spacer(1, 12)
    )

    # ========================================================
    # 2. AVERAGE DIMENSION SCORES
    # ========================================================

    story.append(
        Paragraph(
            "2. Average Evaluation Scores",
            heading_style
        )
    )

    score_data = [
        [
            "Evaluation Dimension",
            "Average Score"
        ],
        [
            "Relevance",
            pdf_score(avg_relevance)
        ],
        [
            "Factuality",
            pdf_score(avg_factuality)
        ],
        [
            "Faithfulness",
            pdf_score(avg_faithfulness)
        ],
        [
            "Completeness",
            pdf_score(avg_completeness)
        ],
        [
            "Semantic Similarity",
            pdf_score(avg_semantic_similarity)
        ],
        [
            "Overall Score",
            pdf_score(avg_overall_score)
        ],
        [
            "Weighted Score",
            pdf_score(avg_weighted_score)
        ],
    ]

    score_table = Table(
        score_data,
        colWidths=[280, 170]
    )

    score_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#222222")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    story.append(score_table)

    story.append(
        Spacer(1, 12)
    )

    # ========================================================
    # 3. HALLUCINATION ANALYSIS
    # ========================================================

    story.append(
        Paragraph(
            "3. Hallucination Analysis",
            heading_style
        )
    )

    hallucination_data = [
        ["Metric", "Count"],
        [
            "Responses with Hallucinations",
            str(hallucination_count)
        ],
        [
            "Responses without Hallucinations",
            str(not_detected_count)
        ],
        [
            "Uncertain Hallucination Status",
            str(uncertain_hallucination_count)
        ],
        [
            "Unsupported Claims",
            str(unsupported_claim_count)
        ],
    ]

    hallucination_table = Table(
        hallucination_data,
        colWidths=[300, 150]
    )

    hallucination_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#222222")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    story.append(
        hallucination_table
    )

    story.append(
        Spacer(1, 12)
    )

    # ========================================================
    # 4. COMPLETENESS ANALYSIS
    # ========================================================

    story.append(
        Paragraph(
            "4. Completeness Analysis",
            heading_style
        )
    )

    completeness_data = [
        ["Metric", "Count"],
        [
            "Missing Aspects",
            str(missing_aspects_count)
        ],
        [
            "Partial Aspects",
            str(partial_aspects_count)
        ],
    ]

    completeness_table = Table(
        completeness_data,
        colWidths=[300, 150]
    )

    completeness_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#222222")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
        ])
    )

    story.append(
        completeness_table
    )

    story.append(
        Spacer(1, 12)
    )

    # ========================================================
    # 5. RECOMMENDATIONS
    # ========================================================

    story.append(
        Paragraph(
            "5. Recommendations",
            heading_style
        )
    )

    recommendations = []

    if fail_count > 0:

        recommendations.append(
            f"- Review {fail_count} failed response(s) "
            "for factuality, relevance, completeness "
            "and hallucination-related issues."
        )

    if needs_count > 0:

        recommendations.append(
            f"- Improve {needs_count} response(s) marked "
            "NEEDS IMPROVEMENT."
        )

    if hallucination_count > 0:

        recommendations.append(
            "- Verify responses containing detected "
            "hallucinations against reliable evidence."
        )

    if uncertain_hallucination_count > 0:

        recommendations.append(
            "- Provide reference answers or knowledge-base "
            "evidence to reduce uncertain hallucination "
            "assessments."
        )

    if missing_aspects_count > 0:

        recommendations.append(
            "- Review missing information identified by "
            "the completeness evaluator."
        )

    if partial_aspects_count > 0:

        recommendations.append(
            "- Improve partially addressed aspects to "
            "increase response completeness."
        )

    if not recommendations:

        recommendations.append(
            "- Batch responses show no major issues "
            "according to the available evaluation results."
        )

    for recommendation in recommendations:

        story.append(
            Paragraph(
                pdf_escape(recommendation),
                normal_style
            )
        )

    story.append(
        PageBreak()
    )

    # ========================================================
    # 6. DETAILED INDIVIDUAL RESULTS
    # ========================================================

    story.append(
        Paragraph(
            "6. Detailed Individual Evaluation Results",
            heading_style
        )
    )

    for position, (_, row) in enumerate(
        df.iterrows()
    ):

        record_number = row.get(
            "Record",
            position + 1
        )

        question = row.get(
            "Question",
            ""
        )

        response = row.get(
            "AI Response",
            ""
        )

        reference = row.get(
            "Reference",
            row.get(
                "Reference Answer",
                ""
            )
        )

        relevance = row.get(
            "Relevance",
            ""
        )

        factuality = row.get(
            "Factuality",
            ""
        )

        faithfulness = row.get(
            "Faithfulness",
            ""
        )

        completeness = row.get(
            "Completeness",
            ""
        )

        semantic_similarity = row.get(
            "Semantic Similarity",
            ""
        )

        overall_score = row.get(
            "Overall Score",
            ""
        )

        weighted_score = row.get(
            "Weighted Score",
            ""
        )

        hallucination = row.get(
            "Hallucination",
            ""
        )

        verdict = row.get(
            "Verdict",
            ""
        )

        error = row.get(
            "Error",
            ""
        )

        # ----------------------------------------------------
        # RECORD
        # ----------------------------------------------------

        story.append(
            Paragraph(
                f"Record {pdf_escape(record_number)}",
                subheading_style
            )
        )

        # ----------------------------------------------------
        # QUESTION
        # ----------------------------------------------------

        story.append(
            Paragraph(
                f"<b>Question:</b> "
                f"{pdf_escape(question)}",
                normal_style
            )
        )

        # ----------------------------------------------------
        # AI RESPONSE
        # ----------------------------------------------------

        story.append(
            Paragraph(
                f"<b>AI Response:</b> "
                f"{pdf_escape(response)}",
                normal_style
            )
        )

        # ----------------------------------------------------
        # REFERENCE ANSWER
        # ----------------------------------------------------

        if pdf_clean_text(reference):

            story.append(
                Paragraph(
                    f"<b>Reference Answer:</b> "
                    f"{pdf_escape(reference)}",
                    normal_style
                )
            )

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if pdf_clean_text(error):

            story.append(
                Paragraph(
                    f"<b>Error:</b> "
                    f"{pdf_escape(error)}",
                    normal_style
                )
            )

        # ----------------------------------------------------
        # INDIVIDUAL SCORE TABLE
        # ----------------------------------------------------

        individual_score_data = [
            [
                "Dimension",
                "Score"
            ],
            [
                "Relevance",
                pdf_score(relevance)
            ],
            [
                "Factuality",
                pdf_score(factuality)
            ],
            [
                "Faithfulness",
                pdf_score(faithfulness)
            ],
            [
                "Completeness",
                pdf_score(completeness)
            ],
            [
                "Semantic Similarity",
                pdf_score(semantic_similarity)
            ],
            [
                "Overall Score",
                pdf_score(overall_score)
            ],
            [
                "Weighted Score",
                pdf_score(weighted_score)
            ],
            [
                "Hallucination",
                pdf_clean_text(hallucination)
                or "N/A"
            ],
            [
                "Verdict",
                pdf_clean_text(verdict)
                or "N/A"
            ],
        ]

        individual_table = Table(
            individual_score_data,
            colWidths=[280, 170]
        )

        individual_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#222222")
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8.5
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
            ])
        )

        story.append(
            individual_table
        )

        story.append(
            Spacer(1, 8)
        )

        # ----------------------------------------------------
        # FULL REPORT
        # ----------------------------------------------------

        full_report = row.get(
            "Full Report",
            None
        )

        if isinstance(
            full_report,
            dict
        ):

            # -----------------------------------------------
            # Evaluation reasoning
            # -----------------------------------------------

            evaluation_reasoning = full_report.get(
                "evaluation_reasoning",
                {}
            )

            if isinstance(
                evaluation_reasoning,
                dict
            ) and evaluation_reasoning:

                story.append(
                    Paragraph(
                        "Evaluation Reasoning",
                        subheading_style
                    )
                )

                for key, value in evaluation_reasoning.items():

                    story.append(
                        Paragraph(
                            f"<b>{pdf_escape(key)}:</b> "
                            f"{pdf_escape(value)}",
                            small_style
                        )
                    )

            # -----------------------------------------------
            # Hallucination details
            # -----------------------------------------------

            hallucination_data = full_report.get(
                "hallucination",
                {}
            )

            if isinstance(
                hallucination_data,
                dict
            ):

                story.append(
                    Paragraph(
                        "Hallucination Details",
                        subheading_style
                    )
                )

                hallucination_explanation = (
                    hallucination_data.get(
                        "explanation",
                        ""
                    )
                )

                if hallucination_explanation:

                    story.append(
                        Paragraph(
                            f"<b>Explanation:</b> "
                            f"{pdf_escape(hallucination_explanation)}",
                            small_style
                        )
                    )

                unsupported_claims = (
                    hallucination_data.get(
                        "unsupported_claims",
                        []
                    )
                )

                if isinstance(
                    unsupported_claims,
                    list
                ) and unsupported_claims:

                    story.append(
                        Paragraph(
                            "<b>Unsupported Claims:</b>",
                            small_style
                        )
                    )

                    for claim in unsupported_claims:

                        story.append(
                            Paragraph(
                                f"- {pdf_escape(claim)}",
                                small_style
                            )
                        )

                contradicted_claims = (
                    hallucination_data.get(
                        "contradicted_claims",
                        []
                    )
                )

                if isinstance(
                    contradicted_claims,
                    list
                ) and contradicted_claims:

                    story.append(
                        Paragraph(
                            "<b>Contradicted Claims:</b>",
                            small_style
                        )
                    )

                    for claim in contradicted_claims:

                        story.append(
                            Paragraph(
                                f"- {pdf_escape(claim)}",
                                small_style
                            )
                        )

            # -----------------------------------------------
            # Completeness details
            # -----------------------------------------------

            completeness_data = full_report.get(
                "completeness",
                {}
            )

            if isinstance(
                completeness_data,
                dict
            ):

                details = completeness_data.get(
                    "details",
                    {}
                )

                story.append(
                    Paragraph(
                        "Completeness Details",
                        subheading_style
                    )
                )

                if isinstance(
                    details,
                    dict
                ):

                    addressed_aspects = details.get(
                        "addressed_aspects",
                        []
                    )

                    partial_aspects = details.get(
                        "partial_aspects",
                        []
                    )

                    missing_aspects = details.get(
                        "missing_aspects",
                        []
                    )

                    reasoning = details.get(
                        "reasoning",
                        ""
                    )

                    if addressed_aspects:

                        story.append(
                            Paragraph(
                                "<b>Addressed Aspects:</b> "
                                + pdf_escape(
                                    addressed_aspects
                                ),
                                small_style
                            )
                        )

                    if partial_aspects:

                        story.append(
                            Paragraph(
                                "<b>Partial Aspects:</b> "
                                + pdf_escape(
                                    partial_aspects
                                ),
                                small_style
                            )
                        )

                    if missing_aspects:

                        story.append(
                            Paragraph(
                                "<b>Missing Aspects:</b> "
                                + pdf_escape(
                                    missing_aspects
                                ),
                                small_style
                            )
                        )

                    if reasoning:

                        story.append(
                            Paragraph(
                                "<b>Completeness Reasoning:</b> "
                                + pdf_escape(
                                    reasoning
                                ),
                                small_style
                            )
                        )

            # -----------------------------------------------
            # Final verdict reasoning
            # -----------------------------------------------

            verdict_reasoning = full_report.get(
                "verdict_consolidated_reasoning",
                full_report.get(
                    "final_assessment",
                    ""
                )
            )

            if verdict_reasoning:

                story.append(
                    Paragraph(
                        "Final Verdict Reasoning",
                        subheading_style
                    )
                )

                story.append(
                    Paragraph(
                        pdf_escape(
                            verdict_reasoning
                        ),
                        small_style
                    )
                )

            # -----------------------------------------------
            # Retrieved context / evidence
            # -----------------------------------------------

            retrieved_context = full_report.get(
                "retrieved_context",
                []
            )

            if isinstance(
                retrieved_context,
                list
            ) and retrieved_context:

                story.append(
                    Paragraph(
                        "Retrieved Evidence / Context",
                        subheading_style
                    )
                )

                for context_item in retrieved_context:

                    story.append(
                        Paragraph(
                            pdf_escape(
                                context_item
                            ),
                            small_style
                        )
                    )

        # ----------------------------------------------------
        # FULL REPORT FALLBACK
        # ----------------------------------------------------

        elif pdf_clean_text(full_report):

            story.append(
                Paragraph(
                    "Evaluation Report",
                    subheading_style
                )
            )

            story.append(
                Paragraph(
                    pdf_escape(full_report),
                    small_style
                )
            )

        story.append(
            Spacer(1, 15)
        )

        # ----------------------------------------------------
        # PAGE BREAK
        # ----------------------------------------------------

        if position < len(df) - 1:

            story.append(
                PageBreak()
            )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

if not st.session_state.get("auth_token"):
    show_auth_page()
    st.stop()

try:
    current_user_response = requests.get(
        f"{AUTH_URL}/me",
        headers=auth_headers(),
        timeout=API_TIMEOUT,
    )
except requests.RequestException as error:
    st.error(api_request_error(error, "validate your session"))
    st.stop()

if current_user_response.status_code == 401:
    clear_auth_state()
    st.rerun()
if not current_user_response.ok:
    st.error(api_response_error(current_user_response, "validate your session"))
    st.stop()
st.session_state.auth_user = current_user_response.json()

st.sidebar.title(
    "AegisEval"
)
st.sidebar.caption(f"Signed in as {st.session_state.auth_user['full_name']}")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🔍 Single Evaluation",
        "📊 Batch Evaluation",
        "📋 Results",
        "📜 History",
        "ℹ️ About",
    ],
)

if st.sidebar.button("Log out", width="stretch"):
    try:
        logout_response = requests.post(
            f"{AUTH_URL}/logout",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        logout_response.raise_for_status()
        clear_auth_state()
        st.rerun()
    except requests.RequestException as error:
        st.sidebar.error(api_request_error(error, "log out"))


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">'
        'AegisEval Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    render_account_dashboard()

    st.markdown(
        '<div class="sub-title">'
        "Automated evaluation, scoring and "
        "hallucination detection"
        "</div>",
        unsafe_allow_html=True
    )

    if st.session_state.batch_results is None:

        st.info(
            "No batch evaluation results available. "
            "Run a Batch Evaluation first."
        )

        st.markdown("---")

        st.markdown(
            "## 📊 Dashboard Metrics"
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Responses",
            "0"
        )

        c2.metric(
            "PASS",
            "0"
        )

        c3.metric(
            "Needs Improvement",
            "0"
        )

        c4.metric(
            "FAIL",
            "0"
        )

    else:

        df = (
            st.session_state
            .batch_results
            .copy()
        )

        if df.empty:

            st.warning(
                "Batch results are empty."
            )

        else:

            # ====================================================
            # CLEAN DATA
            # ====================================================

            if "Verdict" in df.columns:

                df["Verdict"] = (
                    df["Verdict"]
                    .apply(clean_verdict)
                )

            numeric_columns = [
                "Relevance",
                "Factuality",
                "Faithfulness",
                "Completeness",
                "Semantic Similarity",
                "Overall Score",
                "Weighted Score",
            ]

            for column in numeric_columns:

                if column in df.columns:

                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )

            # ====================================================
            # FILTERS
            # ====================================================

            st.sidebar.markdown("---")

            st.sidebar.subheader(
                "🔎 Dashboard Filters"
            )

            if "Verdict" in df.columns:

                available_verdicts = sorted(
                    df["Verdict"]
                    .dropna()
                    .unique()
                    .tolist()
                )

                selected_verdicts = (
                    st.sidebar.multiselect(
                        "Filter by Verdict",
                        available_verdicts,
                        default=available_verdicts,
                    )
                )

            else:

                selected_verdicts = []

            filtered_df = df.copy()

            if (
                selected_verdicts
                and "Verdict"
                in filtered_df.columns
            ):

                filtered_df = filtered_df[
                    filtered_df[
                        "Verdict"
                    ].isin(
                        selected_verdicts
                    )
                ]

            # ====================================================
            # SCORE FILTER
            # ====================================================

            score_column = None

            if "Weighted Score" in filtered_df.columns:

                score_column = (
                    "Weighted Score"
                )

            elif "Overall Score" in filtered_df.columns:

                score_column = (
                    "Overall Score"
                )

            if score_column:

                score_values = pd.to_numeric(
                    filtered_df[
                        score_column
                    ],
                    errors="coerce"
                ).dropna()

                if not score_values.empty:

                    min_score = float(
                        score_values.min()
                    )

                    max_score = float(
                        score_values.max()
                    )

                    if min_score == max_score:

                        max_score = (
                            min_score + 0.01
                        )

                    selected_range = (
                        st.sidebar.slider(
                            "Score Range",
                            min_value=0.0,
                            max_value=10.0,
                            value=(
                                max(
                                    0.0,
                                    min_score
                                ),
                                min(
                                    10.0,
                                    max_score
                                )
                            ),
                        )
                    )

                    filtered_df = filtered_df[
                        (
                            pd.to_numeric(
                                filtered_df[
                                    score_column
                                ],
                                errors="coerce"
                            )
                            >= selected_range[0]
                        )
                        &
                        (
                            pd.to_numeric(
                                filtered_df[
                                    score_column
                                ],
                                errors="coerce"
                            )
                            <= selected_range[1]
                        )
                    ]

            # ====================================================
            # OVERALL STATISTICS
            # ====================================================

            st.markdown(
                "## 📈 Overall Statistics"
            )

            total_responses = len(
                filtered_df
            )

            pass_count = 0
            improvement_count = 0
            fail_count = 0

            if "Verdict" in filtered_df.columns:

                pass_count = len(
                    filtered_df[
                        filtered_df[
                            "Verdict"
                        ] == "PASS"
                    ]
                )

                improvement_count = len(
                    filtered_df[
                        filtered_df[
                            "Verdict"
                        ]
                        == "NEEDS IMPROVEMENT"
                    ]
                )

                fail_count = len(
                    filtered_df[
                        filtered_df[
                            "Verdict"
                        ] == "FAIL"
                    ]
                )

            pass_percentage = (
                pass_count
                / total_responses
                * 100
                if total_responses
                else 0
            )

            improvement_percentage = (
                improvement_count
                / total_responses
                * 100
                if total_responses
                else 0
            )

            fail_percentage = (
                fail_count
                / total_responses
                * 100
                if total_responses
                else 0
            )

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            c1.metric(
                "Total Responses",
                total_responses
            )

            c2.metric(
                "PASS",
                f"{pass_count} "
                f"({pass_percentage:.1f}%)"
            )

            c3.metric(
                "Needs Improvement",
                f"{improvement_count} "
                f"({improvement_percentage:.1f}%)"
            )

            c4.metric(
                "FAIL",
                f"{fail_count} "
                f"({fail_percentage:.1f}%)"
            )

            # ====================================================
            # AVERAGE DIMENSIONS
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 🎯 Average Dimension Scores"
            )

            dimensions = [
                "Relevance",
                "Factuality",
                "Faithfulness",
                "Completeness",
                "Semantic Similarity",
            ]

            dimension_values = {}

            for dimension in dimensions:

                dimension_values[
                    dimension
                ] = safe_average(
                    filtered_df,
                    dimension
                )

            cols = st.columns(
                len(dimensions)
            )

            for i, dimension in enumerate(
                dimensions
            ):

                cols[i].metric(
                    dimension,
                    format_score(
                        dimension_values[
                            dimension
                        ]
                    )
                )

            # ====================================================
            # OVERALL SCORES
            # ====================================================

            st.markdown("---")

            c1, c2 = st.columns(2)

            c1.metric(
                "Average Weighted Score",
                format_score(
                    safe_average(
                        filtered_df,
                        "Weighted Score"
                    )
                )
            )

            c2.metric(
                "Average Overall Score",
                format_score(
                    safe_average(
                        filtered_df,
                        "Overall Score"
                    )
                )
            )

            # ====================================================
            # HALLUCINATION ANALYSIS
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 🚨 Hallucination Analysis"
            )

            hallucination_count = 0
            uncertain_count = 0
            unsupported_claim_count = 0

            for _, row in filtered_df.iterrows():

                status = str(
                    row.get(
                        "Hallucination",
                        ""
                    )
                ).lower()

                if status == "detected":

                    hallucination_count += 1

                elif status == "uncertain":

                    uncertain_count += 1

                report = row.get(
                    "Full Report",
                    {}
                )

                if isinstance(
                    report,
                    dict
                ):

                    hallucination_data = (
                        report.get(
                            "hallucination",
                            {}
                        )
                    )

                    if isinstance(
                        hallucination_data,
                        dict
                    ):

                        claims = (
                            hallucination_data.get(
                                "unsupported_claims",
                                []
                            )
                        )

                        if isinstance(
                            claims,
                            list
                        ):

                            unsupported_claim_count += (
                                len(claims)
                            )

            hc1, hc2, hc3 = (
                st.columns(3)
            )

            hc1.metric(
                "Responses with Hallucinations",
                hallucination_count
            )

            hc2.metric(
                "Uncertain Hallucination Status",
                uncertain_count
            )

            hc3.metric(
                "Unsupported Claims",
                unsupported_claim_count
            )

            # ====================================================
            # COMPLETENESS
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 🧩 Completeness Analysis"
            )

            missing_count = 0
            partial_count = 0

            for _, row in filtered_df.iterrows():

                report = row.get(
                    "Full Report",
                    {}
                )

                if isinstance(
                    report,
                    dict
                ):

                    completeness_data = (
                        report.get(
                            "completeness",
                            {}
                        )
                    )

                    if isinstance(
                        completeness_data,
                        dict
                    ):

                        details = (
                            completeness_data.get(
                                "details",
                                {}
                            )
                        )

                        if isinstance(
                            details,
                            dict
                        ):

                            missing = (
                                details.get(
                                    "missing_aspects",
                                    []
                                )
                            )

                            partial = (
                                details.get(
                                    "partial_aspects",
                                    []
                                )
                            )

                            if isinstance(
                                missing,
                                list
                            ):

                                missing_count += (
                                    len(missing)
                                )

                            if isinstance(
                                partial,
                                list
                            ):

                                partial_count += (
                                    len(partial)
                                )

            cc1, cc2 = st.columns(2)

            cc1.metric(
                "Missing / Incomplete Aspects",
                missing_count
            )

            cc2.metric(
                "Partial Aspects",
                partial_count
            )

            # ====================================================
            # FREQUENT ISSUES
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 🚨 Most Frequent Evaluation Issues"
            )

            issue_counts = {
                "Low Factuality": 0,
                "Low Relevance": 0,
                "Incomplete Response": 0,
                "Hallucination Detected": 0,
            }

            for _, row in filtered_df.iterrows():

                try:

                    factuality = float(
                        row.get(
                            "Factuality"
                        )
                    )

                    if factuality < 7:

                        issue_counts[
                            "Low Factuality"
                        ] += 1

                except Exception:
                    pass

                try:

                    relevance = float(
                        row.get(
                            "Relevance"
                        )
                    )

                    if relevance < 7:

                        issue_counts[
                            "Low Relevance"
                        ] += 1

                except Exception:
                    pass

                try:

                    completeness = float(
                        row.get(
                            "Completeness"
                        )
                    )

                    if completeness < 7:

                        issue_counts[
                            "Incomplete Response"
                        ] += 1

                except Exception:
                    pass

                if str(
                    row.get(
                        "Hallucination",
                        ""
                    )
                ).lower() == "detected":

                    issue_counts[
                        "Hallucination Detected"
                    ] += 1

            issue_df = pd.DataFrame(
                {
                    "Issue": list(
                        issue_counts.keys()
                    ),
                    "Count": list(
                        issue_counts.values()
                    ),
                }
            )

            st.dataframe(
                issue_df,
                width="stretch",
                hide_index=True,
            )

            st.bar_chart(
                issue_df,
                x="Issue",
                y="Count",
            )

            # ====================================================
            # SCORE DISTRIBUTION
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 📊 Score Distribution"
            )

            available_dimensions = [
                column
                for column in dimensions
                if column in filtered_df.columns
            ]

            if available_dimensions:

                distribution_df = (
                    filtered_df[
                        available_dimensions
                    ].copy()
                )

                st.bar_chart(
                    distribution_df
                )

            # ====================================================
            # VERDICT DISTRIBUTION
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 📌 Verdict Distribution"
            )

            if "Verdict" in filtered_df.columns:

                verdict_counts = (
                    filtered_df[
                        "Verdict"
                    ]
                    .value_counts()
                    .rename_axis(
                        "Verdict"
                    )
                    .reset_index(
                        name="Count"
                    )
                )

                st.bar_chart(
                    verdict_counts,
                    x="Verdict",
                    y="Count",
                )

            # ====================================================
            # INDIVIDUAL RESULTS
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 📋 Individual Evaluation Results"
            )

            display_columns = [
                "Record",
                "Question",
                "Relevance",
                "Factuality",
                "Faithfulness",
                "Completeness",
                "Semantic Similarity",
                "Overall Score",
                "Weighted Score",
                "Hallucination",
                "Verdict",
            ]

            available_display_columns = [
                column
                for column in display_columns
                if column in filtered_df.columns
            ]

            st.dataframe(
                filtered_df[
                    available_display_columns
                ],
                width="stretch",
                hide_index=True,
            )

            # ====================================================
            # DRILL DOWN
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 🔍 Drill Down into Individual Result"
            )

            if (
                "Record" in filtered_df.columns
                and not filtered_df.empty
            ):

                record_options = (
                    filtered_df[
                        "Record"
                    ]
                    .dropna()
                    .tolist()
                )

                if record_options:

                    selected_record = (
                        st.selectbox(
                            "Select Record",
                            record_options,
                        )
                    )

                    selected_rows = (
                        filtered_df[
                            filtered_df[
                                "Record"
                            ]
                            == selected_record
                        ]
                    )

                    if not selected_rows.empty:

                        selected_row = (
                            selected_rows.iloc[0]
                        )

                        st.markdown(
                            "### Question"
                        )

                        st.write(
                            selected_row.get(
                                "Question",
                                "N/A"
                            )
                        )

                        st.markdown(
                            "### AI Response"
                        )

                        st.write(
                            selected_row.get(
                                "AI Response",
                                "N/A"
                            )
                        )

                        d1, d2, d3, d4 = (
                            st.columns(4)
                        )

                        d1.metric(
                            "Relevance",
                            format_score(
                                selected_row.get(
                                    "Relevance"
                                )
                            )
                        )

                        d2.metric(
                            "Factuality",
                            format_score(
                                selected_row.get(
                                    "Factuality"
                                )
                            )
                        )

                        d3.metric(
                            "Completeness",
                            format_score(
                                selected_row.get(
                                    "Completeness"
                                )
                            )
                        )

                        d4.metric(
                            "Verdict",
                            selected_row.get(
                                "Verdict",
                                "N/A"
                            )
                        )

                        report = (
                            selected_row.get(
                                "Full Report",
                                {}
                            )
                        )

                        if isinstance(
                            report,
                            dict
                        ):

                            st.markdown(
                                "### 🚨 Hallucination Details"
                            )

                            st.json(
                                report.get(
                                    "hallucination",
                                    {}
                                )
                            )

                            st.markdown(
                                "### 🧩 Completeness Details"
                            )

                            st.json(
                                report.get(
                                    "completeness",
                                    {}
                                )
                            )

                            st.markdown(
                                "### ⚖️ Final Verdict"
                            )

                            st.write(
                                report.get(
                                    "verdict_consolidated_reasoning",
                                    report.get(
                                        "final_assessment",
                                        "N/A"
                                    )
                                )
                            )

                            with st.expander(
                                "View Complete Evaluation Report"
                            ):

                                st.json(
                                    report
                                )

            # ====================================================
            # DOWNLOAD DASHBOARD DATA
            # ====================================================

            st.markdown("---")

            st.markdown(
                "## 📥 Download Dashboard Data"
            )

            download_df = (
                filtered_df.copy()
            )

            if "Full Report" in download_df.columns:

                download_df = download_df.drop(
                    columns=[
                        "Full Report"
                    ]
                )

            st.download_button(
                label="⬇️ Download Results CSV",
                data=download_df.to_csv(
                    index=False
                ),
                file_name=(
                    "llm_evaluation_results.csv"
                ),
                mime="text/csv",
                width="stretch",
            )


# ============================================================
# SINGLE EVALUATION
# ============================================================

elif page == "🔍 Single Evaluation":

    st.title(
        "🔍 Single Response Evaluation"
    )

    question = st.text_area(
        "Question",
        placeholder="Enter the question..."
    )

    response = st.text_area(
        "AI Response",
        placeholder=(
            "Enter the AI-generated response..."
        )
    )

    reference_answer = st.text_area(
        "Reference Answer (Optional)",
        placeholder=(
            "Enter reference answer if available..."
        )
    )

    source_document = st.text_area(
        "Source / Evidence (Optional)",
        placeholder=(
            "Enter supporting evidence if available..."
        )
    )

    use_kb = st.checkbox(
        "Use Knowledge Base",
        value=False
    )
    st.caption(
        "Knowledge Base retrieval is optional and may take longer on its first use while the embedding model loads."
    )

    top_k = st.number_input(
        "Top K Retrieved Documents",
        min_value=1,
        max_value=10,
        value=3
    )

    if st.button(
        "🚀 Evaluate Response",
        width="stretch"
    ):

        if not question.strip():

            st.error(
                "Please enter a question."
            )

        elif not response.strip():

            st.error(
                "Please enter an AI response."
            )

        else:
            payload = {
              "question": question,
              "response": response,
              "reference_answer": reference_answer,
              "source_document": source_document,
              "use_knowledge_base": use_kb,
              "top_k": int(top_k),
            }


            try:

                with st.spinner(
                    "Running evaluation..."
                ):

                    api_response = requests.post(
                        API_URL,
                        json=payload,
                        headers=auth_headers(),
                        timeout=API_TIMEOUT,
                    )

                if api_response.status_code == 200:

                    data = api_response.json()

                    st.session_state.single_result = (
                        data
                    )

                    st.success(
                        "Evaluation completed successfully."
                    )

                    st.markdown(
                        "## 🎯 Evaluation Scores"
                    )

                    s1, s2, s3, s4 = (
                        st.columns(4)
                    )

                    s1.metric(
                        "Relevance",
                        format_score(
                            normalize_score(
                                data.get(
                                    "relevance"
                                )
                            )
                        )
                    )

                    s2.metric(
                        "Accuracy (Factuality)",
                        format_score(
                            normalize_score(
                                data.get(
                                    "factuality"
                                )
                            )
                        )
                    )

                    s3.metric(
                        "Completeness",
                        format_score(
                            normalize_score(
                                data.get(
                                    "completeness"
                                )
                            )
                        )
                    )

                    s4.metric(
                        "Overall Score",
                        format_score(
                            get_value(
                                data,
                                [
                                    "verdict_overall_score",
                                    "overall_score",
                                ]
                            )
                        )
                    )

                    render_single_result_charts(data)

                    st.markdown("---")

                    st.markdown(
                        "## 🚨 Hallucination Detection"
                    )

                    st.json(
                        data.get(
                            "hallucination",
                            {}
                        )
                    )

                    st.markdown("---")

                    st.markdown(
                        "## 🧩 Completeness Evaluation"
                    )

                    st.json(
                        data.get(
                            "completeness",
                            {}
                        )
                    )

                    st.markdown("---")

                    st.markdown(
                        "## ⚖️ Final Verdict"
                    )

                    verdict = data.get(
                        "verdict",
                        "N/A"
                    )

                    st.subheader(
                        clean_verdict(verdict)
                    )

                    st.metric("Evaluation verdict", clean_verdict(verdict))

                    st.write(
                        data.get(
                            "verdict_consolidated_reasoning",
                            data.get(
                                "final_assessment",
                                "N/A"
                            )
                        )
                    )

                    with st.expander(
                        "View Complete Evaluation Report"
                    ):

                        st.json(
                            data
                        )

                else:
                    st.error(api_response_error(api_response, "evaluate this response"))

            except requests.RequestException as error:
                st.error(api_request_error(error, "evaluate this response"))

            except Exception as e:

                st.error(
                    f"Unexpected error: {e}"
                )


# ============================================================
# BATCH EVALUATION
# ============================================================

elif page == "📊 Batch Evaluation":

    st.title(
        "📊 Batch Evaluation"
    )

    st.write(
        "Upload a CSV file containing multiple "
        "questions and AI responses."
    )

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"]
    )

    if uploaded_file is None:

        st.info(
            "Please upload a CSV file to start "
            "batch evaluation."
        )

    else:

        try:

            batch_df = pd.read_csv(
                uploaded_file
            )

            if batch_df.empty:

                st.error(
                    "The uploaded CSV is empty."
                )

            else:

                st.markdown(
                    "### 📄 Uploaded Data"
                )

                st.dataframe(
                    batch_df,
                    width="stretch",
                    hide_index=True,
                )

                # ====================================================
                # COLUMN DETECTION
                # ====================================================

                question_column = None
                response_column = None
                reference_column = None

                possible_question_columns = [
                    "Question",
                    "question",
                    "Query",
                    "query",
                ]

                possible_response_columns = [
                    "AI Response",
                    "ai_response",
                    "Response",
                    "response",
                    "Answer",
                    "answer",
                ]

                possible_reference_columns = [
                    "Reference",
                    "reference",
                    "Reference Answer",
                    "reference_answer",
                ]

                for column in possible_question_columns:

                    if column in batch_df.columns:

                        question_column = (
                            column
                        )
                        break

                for column in possible_response_columns:

                    if column in batch_df.columns:

                        response_column = (
                            column
                        )
                        break

                for column in possible_reference_columns:

                    if column in batch_df.columns:

                        reference_column = (
                            column
                        )
                        break

                # ====================================================
                # VALIDATION
                # ====================================================

                if question_column is None:

                    st.error(
                        "CSV must contain a "
                        "Question column."
                    )

                elif response_column is None:

                    st.error(
                        "CSV must contain an "
                        "AI Response column."
                    )

                else:

                    st.success(
                        f"Detected Question column: "
                        f"{question_column}"
                    )

                    st.success(
                        f"Detected Response column: "
                        f"{response_column}"
                    )

                    if reference_column:

                        st.info(
                            f"Detected Reference column: "
                            f"{reference_column}"
                        )

                    else:

                        st.info(
                            "No Reference column detected. "
                            "Evaluation will continue without "
                            "reference answers."
                        )

                    # ====================================================
                    # RUN BUTTON
                    # ====================================================

                    st.markdown("---")

                    st.markdown(
                        "### 🚀 Start Batch Evaluation"
                    )

                    st.write(
                        f"Ready to evaluate "
                        f"**{len(batch_df)} records**."
                    )

                    run_batch = st.button(
                        "🚀 Run Batch Evaluation",
                        width="stretch",
                        type="primary",
                    )

                    # ====================================================
                    # START EVALUATION
                    # ====================================================

                    if run_batch:

                        results = []

                        total_records = len(
                            batch_df
                        )

                        progress_bar = (
                            st.progress(0)
                        )

                        status_text = st.empty()

                        # --------------------------------------------
                        # RECORD LOOP
                        # --------------------------------------------

                        for index, row in (
                            batch_df.iterrows()
                        ):

                            record_number = (
                                index + 1
                            )

                            status_text.write(
                                f"Evaluating record "
                                f"{record_number} of "
                                f"{total_records}..."
                            )

                            question_value = str(
                                row.get(
                                    question_column,
                                    ""
                                )
                            ).strip()

                            response_value = str(
                                row.get(
                                    response_column,
                                    ""
                                )
                            ).strip()

                            reference_value = ""

                            if reference_column:

                                reference_value = str(
                                    row.get(
                                        reference_column,
                                        ""
                                    )
                                ).strip()

                            # ----------------------------------------
                            # VALIDATE QUESTION
                            # ----------------------------------------

                            if (
                                not question_value
                                or question_value.lower()
                                == "nan"
                            ):

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": "",
                                        "AI Response": response_value,
                                        "Verdict": "ERROR",
                                        "Error": (
                                            "Question is missing."
                                        ),
                                    }
                                )

                                progress_bar.progress(
                                    record_number
                                    / total_records
                                )

                                continue

                            # ----------------------------------------
                            # VALIDATE RESPONSE
                            # ----------------------------------------

                            if (
                                not response_value
                                or response_value.lower()
                                == "nan"
                            ):

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": question_value,
                                        "AI Response": "",
                                        "Verdict": "ERROR",
                                        "Error": (
                                            "AI Response is missing."
                                        ),
                                    }
                                )

                                progress_bar.progress(
                                    record_number
                                    / total_records
                                )

                                continue

                            # ----------------------------------------
                            # API PAYLOAD
                            # ----------------------------------------
                            payload = {
                                "question": question_value,
                                "response": response_value,
                                "reference_answer": reference_value,
                                "source_document": "",
                                "use_knowledge_base": False,
                                "top_k": 3,
                            }
                            
                            # ----------------------------------------
                            # API CALL
                            # ----------------------------------------

                            try:

                                api_response = requests.post(
                                    API_URL,
                                    json=payload,
                                    headers=auth_headers(),
                                    timeout=API_TIMEOUT,
                                )

                                # ------------------------------------
                                # SUCCESS
                                # ------------------------------------

                                if (
                                    api_response.status_code
                                    == 200
                                ):

                                    data = (
                                        api_response.json()
                                    )

                                    relevance = (
                                        normalize_score(
                                            data.get(
                                                "relevance"
                                            )
                                        )
                                    )

                                    factuality = (
                                        normalize_score(
                                            data.get(
                                                "factuality"
                                            )
                                        )
                                    )

                                    completeness = (
                                        normalize_score(
                                            data.get(
                                                "completeness"
                                            )
                                        )
                                    )

                                    semantic_similarity = (
                                        normalize_score(
                                            data.get(
                                                "semantic_similarity"
                                            )
                                        )
                                    )

                                    overall_score = (
                                        get_value(
                                            data,
                                            [
                                                "overall_score",
                                                "verdict_overall_score",
                                            ]
                                        )
                                    )

                                    weighted_score = (
                                        get_value(
                                            data,
                                            [
                                                "weighted_score",
                                                "Weighted Score",
                                                "verdict_overall_score",
                                            ]
                                        )
                                    )

                                    verdict = (
                                        clean_verdict(
                                            get_value(
                                                data,
                                                [
                                                    "verdict",
                                                    "Verdict",
                                                ]
                                            )
                                        )
                                    )

                                    # --------------------------------
                                    # FAITHFULNESS
                                    # --------------------------------

                                    faithfulness_data = (
                                        data.get(
                                            "faithfulness",
                                            {}
                                        )
                                    )

                                    if isinstance(
                                        faithfulness_data,
                                        dict
                                    ):

                                        faithfulness = (
                                            faithfulness_data.get(
                                                "score"
                                            )
                                        )

                                    else:

                                        faithfulness = (
                                            normalize_score(
                                                faithfulness_data
                                            )
                                        )

                                    # --------------------------------
                                    # HALLUCINATION
                                    # --------------------------------

                                    hallucination_status = (
                                        extract_hallucination_status(
                                            data
                                        )
                                    )

                                    # --------------------------------
                                    # SAVE RESULT
                                    # --------------------------------

                                    results.append(
                                        {
                                            "Record": record_number,
                                            "Question": question_value,
                                            "AI Response": response_value,
                                            "Relevance": relevance,
                                            "Factuality": factuality,
                                            "Faithfulness": faithfulness,
                                            "Completeness": completeness,
                                            "Semantic Similarity": semantic_similarity,
                                            "Overall Score": overall_score,
                                            "Weighted Score": weighted_score,
                                            "Hallucination": hallucination_status,
                                            "Verdict": verdict,
                                            "Full Report": data,
                                        }
                                    )

                                # ------------------------------------
                                # API ERROR
                                # ------------------------------------

                                else:

                                    results.append(
                                        {
                                            "Record": record_number,
                                            "Question": question_value,
                                            "AI Response": response_value,
                                            "Verdict": "ERROR",
                                            "Error": api_response_error(
                                                api_response,
                                                "evaluate this batch item",
                                            ),
                                        }
                                    )

                            # ----------------------------------------
                            # TIMEOUT
                            # ----------------------------------------

                            except requests.exceptions.Timeout as error:

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": question_value,
                                        "AI Response": response_value,
                                        "Verdict": "ERROR",
                                        "Error": (
                                            api_request_error(error, "evaluate this batch item")
                                        ),
                                    }
                                )

                            # ----------------------------------------
                            # CONNECTION ERROR
                            # ----------------------------------------

                            except requests.exceptions.ConnectionError as error:

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": question_value,
                                        "AI Response": response_value,
                                        "Verdict": "ERROR",
                                        "Error": (
                                            api_request_error(error, "evaluate this batch item")
                                        ),
                                    }
                                )

                            # ----------------------------------------
                            # OTHER ERROR
                            # ----------------------------------------

                            except Exception as e:

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": question_value,
                                        "AI Response": response_value,
                                        "Verdict": "ERROR",
                                        "Error": str(e),
                                    }
                                )

                            progress_bar.progress(
                                record_number
                                / total_records
                            )

                        # ====================================================
                        # STORE RESULTS
                        # ====================================================

                        results_df = pd.DataFrame(
                            results
                        )

                        st.session_state.batch_results = (
                            results_df
                        )

                        progress_bar.progress(
                            1.0
                        )

                        status_text.success(
                            "Batch evaluation completed."
                        )

                        st.success(
                            f"Completed evaluation of "
                            f"{total_records} records."
                        )

                        # ====================================================
                        # SHOW BATCH RESULTS
                        # ====================================================

                        st.markdown(
                            "## 📋 Batch Results"
                        )

                        display_columns = [
                            "Record",
                            "Question",
                            "Relevance",
                            "Factuality",
                            "Faithfulness",
                            "Completeness",
                            "Semantic Similarity",
                            "Overall Score",
                            "Weighted Score",
                            "Hallucination",
                            "Verdict",
                            "Error",
                        ]

                        available_columns = [
                            column
                            for column in display_columns
                            if column in results_df.columns
                        ]

                        st.dataframe(
                            results_df[
                                available_columns
                            ],
                            width="stretch",
                            hide_index=True,
                        )

                        render_batch_result_charts(results_df)

                        # ====================================================
                        # CSV DOWNLOAD
                        # ====================================================

                        download_df = (
                            results_df.copy()
                        )

                        if "Full Report" in download_df.columns:

                            download_df = (
                                download_df.drop(
                                    columns=[
                                        "Full Report"
                                    ]
                                )
                            )

                        st.download_button(
                            label=(
                                "⬇️ Download Batch Results"
                            ),
                            data=download_df.to_csv(
                                index=False
                            ),
                            file_name=(
                                "batch_evaluation_results.csv"
                            ),
                            mime="text/csv",
                            width="stretch",
                        )

                        # ====================================================
                        # M4.2 PDF EXPORT
                        # ====================================================

                        st.markdown("---")

                        st.markdown(
                            "## 📄 M4.2 - PDF Batch Summary"
                        )

                        try:

                            pdf_bytes = create_batch_pdf(
                                st.session_state.batch_results
                            )

                            st.download_button(
                                label=(
                                    "📥 Download Batch "
                                    "Evaluation PDF"
                                ),
                                data=pdf_bytes,
                                file_name=(
                                    "llm_batch_evaluation_summary.pdf"
                                ),
                                mime="application/pdf",
                                width="stretch",
                            )

                            st.success(
                                "M4.2 PDF Summary is ready."
                            )

                            st.caption(
                                "The PDF includes batch summary, "
                                "dimension scores, weighted scores, "
                                "verdicts, hallucination analysis, "
                                "completeness analysis, detailed "
                                "evaluation reasoning and "
                                "recommendations."
                            )

                        except Exception as pdf_error:

                            st.error(
                                "Unable to generate PDF: "
                                f"{pdf_error}"
                            )

                        # ====================================================
                        # INFORMATION
                        # ====================================================

                        st.info(
                            "Batch results are now stored. "
                            "Open 🏠 Dashboard to view the "
                            "M4.1 dashboard."
                        )

        except Exception as e:

            st.error(
                f"Unable to read CSV file: {e}"
            )


# ============================================================
# RESULTS
# ============================================================

elif page == "📋 Results":

    st.title(
        "📋 Evaluation Results"
    )

    if st.session_state.batch_results is None:

        st.info(
            "No batch results available yet."
        )

    else:

        results_df = (
            st.session_state.batch_results
        )

        st.dataframe(
            results_df,
            width="stretch",
            hide_index=True,
        )

        render_batch_result_charts(results_df)

        download_df = (
            results_df.copy()
        )

        if "Full Report" in download_df.columns:

            download_df = download_df.drop(
                columns=[
                    "Full Report"
                ]
            )

        st.download_button(
            label="⬇️ Download Results CSV",
            data=download_df.to_csv(
                index=False
            ),
            file_name=(
                "batch_evaluation_results.csv"
            ),
            mime="text/csv",
            width="stretch",
        )

        # ====================================================
        # PDF EXPORT FROM RESULTS PAGE
        # ====================================================

        st.markdown("---")

        st.markdown(
            "## 📄 M4.2 - PDF Batch Summary"
        )

        try:

            pdf_bytes = create_batch_pdf(
                results_df
            )

            st.download_button(
                label=(
                    "📥 Download Batch "
                    "Evaluation PDF"
                ),
                data=pdf_bytes,
                file_name=(
                    "llm_batch_evaluation_summary.pdf"
                ),
                mime="application/pdf",
                width="stretch",
            )

        except Exception as pdf_error:

            st.error(
                f"Unable to generate PDF: "
                f"{pdf_error}"
            )


# ============================================================
# EVALUATION HISTORY
# ============================================================

elif page == "📜 History":

    st.title("Evaluation History")
    try:
        history_response = requests.get(
            f"{AUTH_URL}/history",
            headers=auth_headers(),
            timeout=API_TIMEOUT,
        )
        history_response.raise_for_status()
        evaluations = history_response.json().get("evaluations", [])
    except requests.RequestException as error:
        st.error(api_request_error(error, "load your evaluation history"))
        evaluations = []
    except ValueError as error:
        st.error(f"The API returned invalid history data: {error}")
        evaluations = []

    if evaluations:
        history = pd.DataFrame(evaluations)
        history = history.rename(
            columns={
                "created_at": "Created",
                "question": "Question",
                "response": "AI Response",
                "reference_answer": "Reference Answer",
                "verdict": "Verdict",
                "overall_score": "Overall Score",
            }
        )
        display_columns = [
            column
            for column in (
                "Created",
                "Question",
                "AI Response",
                "Reference Answer",
                "Verdict",
                "Overall Score",
            )
            if column in history.columns
        ]
        st.dataframe(history[display_columns], hide_index=True, use_container_width=True)
    else:
        st.info("No saved evaluations yet. Run an evaluation to start your history.")


# ============================================================
# ABOUT
# ============================================================

elif page == "ℹ️ About":

    st.title(
        "ℹ️ About the System"
    )

    st.markdown(
        """
        ## Automated LLM Evaluation and Hallucination Detection System

        This platform automatically evaluates AI-generated responses
        using multiple evaluation dimensions.

        ### Evaluation Dimensions

        - **Relevance** – checks whether the response addresses the question.
        - **Factuality** – checks factual correctness.
        - **Faithfulness** – checks whether claims are supported by evidence.
        - **Completeness** – checks whether important information is missing.
        - **Semantic Similarity** – compares the response with the reference answer.
        - **Hallucination Detection** – identifies unsupported claims.

        ### Evaluation Workflow

        **Input → Knowledge Base / RAG → Evaluation Agents → Scoring → Verdict → Dashboard**

        ### Verdicts

        - PASS
        - NEEDS IMPROVEMENT
        - FAIL

        ### Milestone 4

        The dashboard provides:

        - Overall response statistics
        - Verdict percentages
        - Average dimension scores
        - Hallucination statistics
        - Completeness statistics
        - Frequent evaluation issues
        - Score visualization
        - Verdict distribution
        - Individual result drill-down
        - CSV export
        - PDF batch summary export
        """
    )