import requests
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="Automated LLM Evaluation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DARK PROFESSIONAL UI
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #080d18;
        color: #e5e7eb;
    }

    .main .block-container {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* SIDEBAR */

    section[data-testid="stSidebar"] {
        background: #060a12;
        border-right: 1px solid #1e293b;
    }

    section[data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    .brand {
        padding: 15px 5px 25px 5px;
        border-bottom: 1px solid #1e293b;
        margin-bottom: 20px;
    }

    .brand-title {
        font-size: 20px;
        font-weight: 800;
        color: #f8fafc;
    }

    .brand-subtitle {
        font-size: 12px;
        color: #64748b;
        margin-top: 5px;
    }

    .sidebar-footer {
        margin-top: 35px;
        padding-top: 20px;
        border-top: 1px solid #1e293b;
        color: #64748b;
        font-size: 11px;
        line-height: 1.6;
    }

    /* HEADERS */

    .hero-title {
        font-size: 36px;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.2;
        margin-bottom: 10px;
    }

    .hero-subtitle {
        font-size: 16px;
        color: #94a3b8;
        margin-bottom: 25px;
    }

    .page-title {
        font-size: 32px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 5px;
    }

    .page-subtitle {
        color: #94a3b8;
        font-size: 15px;
        margin-bottom: 25px;
    }

    /* DASHBOARD CARDS */

    .feature-card {
        background: linear-gradient(
            145deg,
            #111827,
            #0f172a
        );
        border: 1px solid #263449;
        border-radius: 18px;
        padding: 25px;
        min-height: 175px;
        margin-bottom: 18px;
    }

    .feature-icon {
        font-size: 30px;
        margin-bottom: 12px;
    }

    .feature-title {
        color: #f8fafc;
        font-size: 21px;
        font-weight: 750;
        margin-bottom: 8px;
    }

    .feature-text {
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.7;
    }

    /* METRICS */

    [data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #263449;
        border-radius: 14px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
    }

    /* INPUTS */

    textarea,
    input {
        background-color: #111827 !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
    }

    label {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
    }

    /* BUTTONS */

    .stButton > button {
        background: #2563eb;
        color: white;
        border: 1px solid #3b82f6;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 20px;
    }

    .stButton > button:hover {
        background: #1d4ed8;
    }

    /* JUDGE CARDS */

    .judge-card {
        background: #111827;
        border: 1px solid #263449;
        border-radius: 15px;
        padding: 22px;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    .judge-title {
        color: #f8fafc;
        font-size: 20px;
        font-weight: 750;
        margin-bottom: 15px;
    }

    /* VERDICT */

    .verdict-card {
        background: #111827;
        border: 1px solid #263449;
        border-radius: 18px;
        padding: 25px;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .verdict-label {
        color: #94a3b8;
        font-size: 14px;
    }

    .verdict-value {
        color: #f8fafc;
        font-size: 32px;
        font-weight: 800;
    }

    /* DATAFRAME */

    [data-testid="stDataFrame"] {
        border: 1px solid #263449;
        border-radius: 12px;
        overflow: hidden;
    }

    /* EXPANDER */

    details {
        background: #111827 !important;
        border: 1px solid #263449 !important;
        border-radius: 10px !important;
    }

    hr {
        border-color: #263449;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "single_report" not in st.session_state:
    st.session_state.single_report = None

if "batch_results" not in st.session_state:
    st.session_state.batch_results = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            <div class="brand-title">
                🤖 LLM Evaluation
            </div>
            <div class="brand-subtitle">
                AI Response Quality Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🔍 Single Evaluation",
            "📊 Batch Evaluation",
            "📋 Results",
            "ℹ️ About",
        ],
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="sidebar-footer">
            Automated LLM Evaluation and<br>
            Hallucination Detection System<br><br>
            FastAPI + Streamlit + ChromaDB
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="hero-title">
            Automated LLM Evaluation and<br>
            Hallucination Detection System
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="hero-subtitle">
            An intelligent quality-checking platform for
            evaluating AI-generated responses.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Evaluation Platform")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">
                    Single Evaluation
                </div>
                <div class="feature-text">
                    Evaluate one AI-generated response using
                    six evaluation dimensions and receive
                    detailed evidence, reasoning and a final verdict.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:

        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">
                    Batch Evaluation
                </div>
                <div class="feature-text">
                    Upload a CSV containing multiple questions
                    and AI responses. Evaluate all records
                    automatically and download the results.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Evaluation Dimensions")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("01", "Relevance")

    with c2:
        st.metric("02", "Factuality")

    with c3:
        st.metric("03", "Faithfulness")

    c4, c5, c6 = st.columns(3)

    with c4:
        st.metric("04", "Completeness")

    with c5:
        st.metric("05", "Semantic Similarity")

    with c6:
        st.metric("06", "Hallucination")


# ============================================================
# SINGLE EVALUATION
# ============================================================

elif page == "🔍 Single Evaluation":

    st.markdown(
        '<div class="page-title">Single Evaluation</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Evaluate one AI-generated response in detail.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Evaluation Input")

    question = st.text_area(
        "Question",
        placeholder="Enter the question...",
    )

    ai_response = st.text_area(
        "AI Response",
        placeholder="Enter the AI-generated response...",
    )

    reference_answer = st.text_area(
        "Reference Answer (optional)",
        placeholder="Enter the expected answer...",
    )

    source_document = st.text_area(
        "Source Document / Context (optional)",
        placeholder="Enter supporting information...",
    )

    input_col1, input_col2 = st.columns(2)

    with input_col1:

        use_knowledge_base = st.checkbox(
            "Use Knowledge Base",
            value=True,
        )

    with input_col2:

        top_k = st.number_input(
            "Retrieved Chunks",
            min_value=1,
            max_value=10,
            value=1,
            step=1,
        )

    if st.button(
        "🚀 Evaluate Response",
        type="primary",
    ):

        if not question.strip():

            st.error("Please enter a question.")

        elif not ai_response.strip():

            st.error("Please enter an AI response.")

        else:

            payload = {
                "question": question,
                "response": ai_response,
                "reference_answer": (
                    reference_answer
                    if reference_answer.strip()
                    else None
                ),
                "source_document": (
                    source_document
                    if source_document.strip()
                    else None
                ),
                "use_knowledge_base": use_knowledge_base,
                "top_k": int(top_k),
            }

            try:

                result = requests.post(
                    f"{BACKEND_URL}/evaluate",
                    json=payload,
                    timeout=180,
                )

                if result.status_code != 200:

                    st.error(
                        f"Backend error: {result.status_code}"
                    )

                    st.code(result.text)

                else:

                    st.session_state.single_report = result.json()

                    st.success(
                        "Evaluation completed successfully."
                    )

            except requests.exceptions.RequestException as error:

                st.error(
                    "Could not connect to the FastAPI backend."
                )

                st.write(str(error))

            except Exception as error:

                st.error(
                    "An unexpected error occurred."
                )

                st.exception(error)

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    report = st.session_state.single_report

    if report is not None:

        st.divider()

        st.header("Evaluation Results")

        overall_score = report.get("overall_score")

        verdict = report.get(
            "verdict",
            "NEEDS IMPROVEMENT",
        )

        verdict_score = report.get(
            "verdict_overall_score"
        )

        hallucination_data = report.get(
            "hallucination",
            {},
        )

        detected = hallucination_data.get(
            "hallucination_detected"
        )

        if detected is True:
            hallucination_text = "YES"
        elif detected is False:
            hallucination_text = "NO"
        else:
            hallucination_text = "UNCERTAIN"

        top1, top2, top3 = st.columns(3)

        with top1:

            st.metric(
                "Overall Score",
                (
                    f"{overall_score:.2f} / 10"
                    if overall_score is not None
                    else "Unavailable"
                ),
            )

        with top2:

            st.metric(
                "Weighted Score",
                (
                    f"{verdict_score:.2f} / 10"
                    if verdict_score is not None
                    else "Unavailable"
                ),
            )

        with top3:

            st.metric(
                "Hallucination",
                hallucination_text,
            )

        st.subheader("Evaluation Dimensions")

        s1, s2, s3 = st.columns(3)

        with s1:

            score = report.get("relevance_score")

            st.metric(
                "Relevance",
                f"{score:.2f}" if score is not None else "N/A",
            )

        with s2:

            score = report.get("factuality_score")

            st.metric(
                "Factuality",
                f"{score:.2f}" if score is not None else "N/A",
            )

        with s3:

            score = report.get("faithfulness_score")

            st.metric(
                "Faithfulness",
                f"{score:.2f}" if score is not None else "N/A",
            )

        s4, s5 = st.columns(2)

        with s4:

            score = report.get("completeness_score")

            st.metric(
                "Completeness",
                f"{score:.2f}" if score is not None else "N/A",
            )

        with s5:

            score = report.get(
                "semantic_similarity_score"
            )

            st.metric(
                "Semantic Similarity",
                f"{score:.2f}" if score is not None else "N/A",
            )

        # ====================================================
        # RELEVANCE
        # ====================================================

        relevance = report.get(
            "relevance",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">1. Relevance Judge</div>',
            unsafe_allow_html=True,
        )

        relevance_score = relevance.get("score")

        st.write(
            f"**Score:** {relevance_score:.2f} / 10"
            if relevance_score is not None
            else "**Score:** Unavailable"
        )

        details = relevance.get("details", {})

        if details.get("category"):

            st.write(
                f"**Category:** {details['category']}"
            )

        if details.get("reasoning"):

            st.write(
                f"**Reasoning:** {details['reasoning']}"
            )

        if relevance.get("explanation"):

            st.write(
                f"**Explanation:** "
                f"{relevance['explanation']}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # FACTUALITY
        # ====================================================

        factuality = report.get(
            "factuality",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">'
            '2. Accuracy / Factuality Judge'
            '</div>',
            unsafe_allow_html=True,
        )

        factuality_score = factuality.get("score")

        st.write(
            f"**Score:** {factuality_score:.2f} / 10"
            if factuality_score is not None
            else "**Score:** Unavailable"
        )

        details = factuality.get("details", {})

        if details.get("category"):

            st.write(
                f"**Category:** {details['category']}"
            )

        evidence = details.get(
            "supporting_evidence",
            [],
        )

        if evidence:

            st.write("**Supporting Evidence:**")

            for item in evidence:

                st.write(
                    f"- {item}"
                )

        if factuality.get("explanation"):

            st.write(
                f"**Reasoning:** "
                f"{factuality['explanation']}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # FAITHFULNESS
        # ====================================================

        faithfulness = report.get(
            "faithfulness",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">'
            '3. Faithfulness Judge'
            '</div>',
            unsafe_allow_html=True,
        )

        faithfulness_score = faithfulness.get("score")

        st.write(
            f"**Score:** {faithfulness_score:.2f} / 10"
            if faithfulness_score is not None
            else "**Score:** Uncertain"
        )

        details = faithfulness.get("details", {})

        supported = details.get(
            "supported_claims",
            [],
        )

        if supported:

            st.write("**Supported Claims:**")

            for claim in supported:

                st.write(
                    f"- {claim}"
                )

        unsupported = details.get(
            "unsupported_claims",
            [],
        )

        if unsupported:

            st.write("**Unsupported Claims:**")

            for claim in unsupported:

                st.write(
                    f"- {claim}"
                )

        if details.get("certainty"):

            st.write(
                f"**Certainty:** "
                f"{details['certainty']}"
            )

        if faithfulness.get("explanation"):

            st.write(
                f"**Reasoning:** "
                f"{faithfulness['explanation']}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # COMPLETENESS
        # ====================================================

        completeness = report.get(
            "completeness",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">'
            '4. Completeness Judge'
            '</div>',
            unsafe_allow_html=True,
        )

        completeness_score = completeness.get("score")

        st.write(
            f"**Score:** {completeness_score:.2f} / 10"
            if completeness_score is not None
            else "**Score:** Unavailable"
        )

        details = completeness.get("details", {})

        addressed = details.get(
            "addressed_aspects",
            [],
        )

        if addressed:

            st.write("**Addressed Aspects:**")

            for item in addressed:

                st.write(
                    f"- {item}"
                )

        partial = details.get(
            "partial_aspects",
            [],
        )

        if partial:

            st.write(
                "**Partially Addressed Aspects:**"
            )

            for item in partial:

                st.write(
                    f"- {item}"
                )

        missing = details.get(
            "missing_aspects",
            [],
        )

        if missing:

            st.write("**Missing Aspects:**")

            for item in missing:

                st.write(
                    f"- {item}"
                )

        if details.get("missing_information"):

            st.write(
                "**Missing Information:**"
            )

            for item in details[
                "missing_information"
            ]:

                st.write(
                    f"- {item}"
                )

        if details.get("target"):

            st.write(
                f"**Evaluation Target:** "
                f"{details['target']}"
            )

        if details.get("reasoning"):

            st.write(
                f"**Reasoning:** "
                f"{details['reasoning']}"
            )

        if completeness.get("explanation"):

            st.write(
                f"**Explanation:** "
                f"{completeness['explanation']}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # SEMANTIC SIMILARITY
        # ====================================================

        semantic = report.get(
            "semantic_similarity",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">'
            '5. Semantic Similarity Judge'
            '</div>',
            unsafe_allow_html=True,
        )

        semantic_score = semantic.get("score")

        st.write(
            f"**Score:** {semantic_score:.2f} / 10"
            if semantic_score is not None
            else "**Score:** Unavailable"
        )

        details = semantic.get(
            "details",
            {},
        )

        if details.get("similarity") is not None:

            st.write(
                f"**Similarity:** "
                f"{details['similarity']}"
            )

        if details.get("model"):

            st.write(
                f"**Model:** "
                f"{details['model']}"
            )

        if semantic.get("explanation"):

            st.write(
                f"**Reasoning:** "
                f"{semantic['explanation']}"
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # HALLUCINATION
        # ====================================================

        hallucination = report.get(
            "hallucination",
            {},
        )

        st.markdown(
            '<div class="judge-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="judge-title">'
            '6. Hallucination Detection Judge'
            '</div>',
            unsafe_allow_html=True,
        )

        detected = hallucination.get(
            "hallucination_detected"
        )

        severity = hallucination.get(
            "severity"
        )

        if detected is True:

            st.error(
                "Hallucination Detected: YES"
            )

        elif detected is False:

            st.success(
                "Hallucination Detected: NO"
            )

        else:

            st.warning(
                "Hallucination Detection: UNCERTAIN"
            )

        st.write(
            f"**Severity:** "
            f"{severity or 'Uncertain'}"
        )

        unsupported = hallucination.get(
            "unsupported_claims",
            [],
        )

        if unsupported:

            st.write("**Unsupported Claims:**")

            for claim in unsupported:

                st.write(
                    f"- {claim}"
                )

        contradicted = hallucination.get(
            "contradicted_claims",
            [],
        )

        if contradicted:

            st.write("**Contradicted Claims:**")

            for claim in contradicted:

                st.write(
                    f"- {claim}"
                )

        supported = hallucination.get(
            "supported_claims",
            [],
        )

        if supported:

            st.write("**Supported Claims:**")

            for claim in supported:

                st.write(
                    f"- {claim}"
                )

        st.write(
            f"**Explanation:** "
            f"{hallucination.get('explanation', 'Unavailable')}"
        )

        st.write(
            f"**Certainty:** "
            f"{hallucination.get('certainty', 'Unavailable')}"
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        # ====================================================
        # FINAL VERDICT
        # ====================================================

        st.header("Final Verdict")

        if verdict == "PASS":

            st.success("✅ PASS")

        elif verdict == "NEEDS IMPROVEMENT":

            st.warning(
                "⚠️ NEEDS IMPROVEMENT"
            )

        else:

            st.error("❌ FAIL")

        if verdict_score is not None:

            st.metric(
                "Weighted Overall Score",
                f"{verdict_score:.2f} / 10",
            )

        # ====================================================
        # MAJOR ISSUES
        # ====================================================

        major_issues = report.get(
            "verdict_major_issues",
            [],
        )

        if major_issues:

            st.subheader("Major Issues")

            for issue in major_issues:

                st.write(
                    f"- {issue}"
                )

        # ====================================================
        # CONSOLIDATED SUMMARY
        # ====================================================

        st.subheader(
            "Consolidated Evaluation Summary"
        )

        st.write(
            report.get(
                "verdict_consolidated_reasoning",
                "No consolidated reasoning available.",
            )
        )

        # ====================================================
        # FINAL ASSESSMENT
        # ====================================================

        st.subheader(
            "Final Assessment"
        )

        st.write(
            report.get(
                "final_assessment",
                "No final assessment available.",
            )
        )

        # ====================================================
        # RETRIEVED EVIDENCE
        # ====================================================

        retrieved_context = report.get(
            "retrieved_context",
            [],
        )

        if retrieved_context:

            st.header(
                "Retrieved Evidence"
            )

            for index, context in enumerate(
                retrieved_context,
                start=1,
            ):

                with st.expander(
                    f"Evidence {index}"
                ):

                    st.write(context)


# ============================================================
# BATCH EVALUATION
# ============================================================

elif page == "📊 Batch Evaluation":

    st.markdown(
        '<div class="page-title">Batch Evaluation</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Evaluate multiple AI responses automatically using CSV input.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV file",
        type=["csv"],
    )

    if uploaded_file is not None:

        try:

            batch_df = pd.read_csv(
                uploaded_file
            )

            st.subheader(
                "Uploaded Dataset"
            )

            st.dataframe(
                batch_df,
                use_container_width=True,
            )

            required_columns = [
                "question",
                "ai_response",
            ]

            missing_columns = [
                column
                for column in required_columns
                if column not in batch_df.columns
            ]

            if missing_columns:

                st.error(
                    "Missing required columns: "
                    + ", ".join(missing_columns)
                )

            elif batch_df.empty:

                st.warning(
                    "The CSV file is empty."
                )

            else:

                st.success(
                    f"CSV validated successfully. "
                    f"{len(batch_df)} records found."
                )

                if st.button(
                    "🚀 Run Batch Evaluation",
                    type="primary",
                ):

                    results = []

                    progress_bar = st.progress(
                        0
                    )

                    status_text = st.empty()

                    total_records = len(
                        batch_df
                    )

                    for index, row in batch_df.iterrows():

                        record_number = index + 1

                        status_text.write(
                            f"Evaluating record "
                            f"{record_number} of "
                            f"{total_records}..."
                        )

                        payload = {
                            "question": str(
                                row["question"]
                            ),
                            "response": str(
                                row["ai_response"]
                            ),
                            "reference_answer": (
                                str(
                                    row["reference_answer"]
                                )
                                if (
                                    "reference_answer"
                                    in batch_df.columns
                                    and pd.notna(
                                        row["reference_answer"]
                                    )
                                )
                                else None
                            ),
                            "source_document": (
                                str(
                                    row["source_document"]
                                )
                                if (
                                    "source_document"
                                    in batch_df.columns
                                    and pd.notna(
                                        row["source_document"]
                                    )
                                )
                                else None
                            ),
                            "use_knowledge_base": True,
                            "top_k": 1,
                        }

                        try:

                            response = requests.post(
                                f"{BACKEND_URL}/evaluate",
                                json=payload,
                                timeout=180,
                            )

                            if response.status_code == 200:

                                report = response.json()

                                hallucination_data = report.get(
                                    "hallucination",
                                    {},
                                )

                                detected = hallucination_data.get(
                                    "hallucination_detected"
                                )

                                if detected is True:

                                    hallucination_status = "YES"

                                elif detected is False:

                                    hallucination_status = "NO"

                                else:

                                    hallucination_status = "UNCERTAIN"

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": payload[
                                            "question"
                                        ],
                                        "Relevance": report.get(
                                            "relevance_score"
                                        ),
                                        "Factuality": report.get(
                                            "factuality_score"
                                        ),
                                        "Faithfulness": report.get(
                                            "faithfulness_score"
                                        ),
                                        "Completeness": report.get(
                                            "completeness_score"
                                        ),
                                        "Semantic Similarity": report.get(
                                            "semantic_similarity_score"
                                        ),
                                        "Overall Score": report.get(
                                            "overall_score"
                                        ),
                                        "Verdict": report.get(
                                            "verdict"
                                        ),
                                        "Hallucination": (
                                            hallucination_status
                                        ),
                                    }
                                )

                            else:

                                results.append(
                                    {
                                        "Record": record_number,
                                        "Question": payload[
                                            "question"
                                        ],
                                        "Relevance": None,
                                        "Factuality": None,
                                        "Faithfulness": None,
                                        "Completeness": None,
                                        "Semantic Similarity": None,
                                        "Overall Score": None,
                                        "Verdict": "ERROR",
                                        "Hallucination": "ERROR",
                                    }
                                )

                                st.error(
                                    f"Record {record_number} failed: "
                                    f"HTTP {response.status_code}"
                                )

                        except requests.exceptions.RequestException as error:

                            results.append(
                                {
                                    "Record": record_number,
                                    "Question": payload[
                                        "question"
                                    ],
                                    "Relevance": None,
                                    "Factuality": None,
                                    "Faithfulness": None,
                                    "Completeness": None,
                                    "Semantic Similarity": None,
                                    "Overall Score": None,
                                    "Verdict": "ERROR",
                                    "Hallucination": "ERROR",
                                }
                            )

                            st.error(
                                f"Record {record_number} failed: "
                                f"{error}"
                            )

                        progress_bar.progress(
                            record_number / total_records
                        )

                    status_text.success(
                        "Batch evaluation completed successfully."
                    )

                    st.session_state.batch_results = (
                        pd.DataFrame(results)
                    )

        except Exception as error:

            st.error(
                "Could not read the CSV file."
            )

            st.exception(error)

    # ========================================================
    # DISPLAY BATCH RESULTS
    # ========================================================

    if st.session_state.batch_results is not None:

        results_df = st.session_state.batch_results

        st.divider()

        st.subheader(
            "Batch Evaluation Results"
        )

        st.dataframe(
            results_df,
            use_container_width=True,
        )

        successful_results = results_df[
            results_df["Verdict"] != "ERROR"
        ]

        if not successful_results.empty:

            st.subheader(
                "Batch Summary"
            )

            average_score = (
                successful_results[
                    "Overall Score"
                ]
                .dropna()
                .mean()
            )

            pass_count = (
                successful_results[
                    "Verdict"
                ]
                == "PASS"
            ).sum()

            hallucination_count = (
                successful_results[
                    "Hallucination"
                ]
                == "YES"
            ).sum()

            b1, b2, b3 = st.columns(3)

            with b1:

                st.metric(
                    "Average Overall Score",
                    (
                        f"{average_score:.2f}"
                        if pd.notna(average_score)
                        else "N/A"
                    ),
                )

            with b2:

                st.metric(
                    "PASS",
                    int(pass_count),
                )

            with b3:

                st.metric(
                    "Hallucinations Detected",
                    int(hallucination_count),
                )

            st.subheader(
                "Verdict Distribution"
            )

            verdict_counts = (
                successful_results[
                    "Verdict"
                ]
                .value_counts()
            )

            st.bar_chart(
                verdict_counts
            )

            csv_data = results_df.to_csv(
                index=False
            )

            st.download_button(
                label="⬇️ Download Batch Results CSV",
                data=csv_data,
                file_name="m3_batch_evaluation_results.csv",
                mime="text/csv",
            )

        else:

            st.warning(
                "No records were evaluated successfully."
            )


# ============================================================
# RESULTS PAGE
# ============================================================

elif page == "📋 Results":

    st.markdown(
        '<div class="page-title">Evaluation Results</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Review your latest evaluation outputs.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.single_report is not None:

        st.subheader(
            "Latest Single Evaluation"
        )

        report = st.session_state.single_report

        r1, r2, r3 = st.columns(3)

        with r1:

            score = report.get(
                "overall_score"
            )

            st.metric(
                "Overall Score",
                (
                    f"{score:.2f}"
                    if score is not None
                    else "N/A"
                ),
            )

        with r2:

            st.metric(
                "Verdict",
                report.get(
                    "verdict",
                    "N/A",
                ),
            )

        with r3:

            hallucination = report.get(
                "hallucination",
                {},
            )

            detected = hallucination.get(
                "hallucination_detected"
            )

            if detected is True:

                value = "YES"

            elif detected is False:

                value = "NO"

            else:

                value = "UNCERTAIN"

            st.metric(
                "Hallucination",
                value,
            )

    else:

        st.info(
            "No single evaluation result available yet."
        )

    if st.session_state.batch_results is not None:

        st.divider()

        st.subheader(
            "Latest Batch Evaluation"
        )

        st.dataframe(
            st.session_state.batch_results,
            use_container_width=True,
        )

    else:

        st.info(
            "No batch evaluation result available yet."
        )


# ============================================================
# ABOUT
# ============================================================

elif page == "ℹ️ About":

    st.markdown(
        '<div class="page-title">About the Project</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="page-subtitle">
            Automated quality evaluation of AI-generated responses.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Automated LLM Evaluation and Hallucination Detection System

        This project provides an automated quality-checking system
        for AI-generated responses.

        ### Evaluation Dimensions

        - Relevance
        - Accuracy / Factuality
        - Faithfulness
        - Completeness
        - Semantic Similarity
        - Hallucination Detection

        ### Technology Stack

        - Python
        - Streamlit
        - FastAPI
        - ChromaDB
        - Sentence Transformers
        - Hugging Face Datasets

        ### Main Capabilities

        - Single response evaluation
        - Knowledge-base retrieval
        - Evidence-based evaluation
        - Multi-dimensional scoring
        - Final PASS / NEEDS IMPROVEMENT / FAIL verdict
        - Batch CSV evaluation
        - Batch result summary
        - Downloadable CSV results
        """
    )