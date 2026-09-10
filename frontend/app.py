
import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Automated LLM Evaluation",
    page_icon="🤖",
    layout="wide",
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown(
    """
    <style>

    .main-title {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        margin-bottom: 25px;
    }

    .judge-box {
        border: 1px solid #d9d9d9;
        border-radius: 10px;
        padding: 18px;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    .judge-title {
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.markdown(
    '<div class="main-title">'
    'Automated LLM Evaluation and Hallucination Detection System'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Evaluate AI-generated responses using multiple evaluation judges.'
    '</div>',
    unsafe_allow_html=True,
)


# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------

st.subheader("Evaluation Input")

question = st.text_area(
    "Question",
    placeholder="Enter the question here...",
)

ai_response = st.text_area(
    "AI Response",
    placeholder="Enter the AI-generated response here...",
)

reference_answer = st.text_area(
    "Reference Answer (optional)",
    placeholder="Enter the expected/reference answer...",
)

source_document = st.text_area(
    "Source Document / Context (optional)",
    placeholder="Enter source information or supporting context...",
)

use_knowledge_base = st.checkbox(
    "Use Knowledge Base",
    value=True,
)

top_k = st.number_input(
    "Retrieved chunks",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
)


# --------------------------------------------------
# EVALUATE BUTTON
# --------------------------------------------------

if st.button(
    "Evaluate Response",
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
                timeout=120,
            )

            if result.status_code != 200:

                st.error(
                    f"Backend error: {result.status_code}"
                )

                st.code(result.text)

            else:

                # --------------------------------------------------
                # REPORT IS CREATED HERE
                # --------------------------------------------------

                report = result.json()


                # --------------------------------------------------
                # OVERALL EVALUATION
                # --------------------------------------------------

                st.header("Overall Evaluation")

                overall_score = report.get(
                    "overall_score"
                )

                if overall_score is not None:

                    st.metric(
                        "Overall Score",
                        f"{overall_score:.2f} / 10",
                    )

                else:

                    st.write(
                        "**Overall Score:** Unavailable"
                    )


                # --------------------------------------------------
                # EVALUATION DIMENSIONS
                # --------------------------------------------------

                st.header("Evaluation Dimensions")

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Relevance",
                        (
                            f"{report['relevance_score']:.2f}"
                            if report.get("relevance_score")
                            is not None
                            else "Unavailable"
                        ),
                    )

                with col2:

                    st.metric(
                        "Factuality",
                        (
                            f"{report['factuality_score']:.2f}"
                            if report.get("factuality_score")
                            is not None
                            else "Unavailable"
                        ),
                    )

                with col3:

                    st.metric(
                        "Faithfulness",
                        (
                            f"{report['faithfulness_score']:.2f}"
                            if report.get("faithfulness_score")
                            is not None
                            else "Uncertain"
                        ),
                    )

                col4, col5 = st.columns(2)

                with col4:

                    st.metric(
                        "Completeness",
                        (
                            f"{report['completeness_score']:.2f}"
                            if report.get("completeness_score")
                            is not None
                            else "Unavailable"
                        ),
                    )

                with col5:

                    st.metric(
                        "Semantic Similarity",
                        (
                            f"{report['semantic_similarity_score']:.2f}"
                            if report.get(
                                "semantic_similarity_score"
                            )
                            is not None
                            else "Unavailable"
                        ),
                    )


                # --------------------------------------------------
                # 1. RELEVANCE JUDGE
                # --------------------------------------------------

                relevance = report["relevance"]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '1. Relevance Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                relevance_score = relevance["score"]

                st.write(
                    f"**Score:** "
                    f"{relevance_score:.2f} / 10"
                    if relevance_score is not None
                    else "**Score:** Unavailable"
                )

                if relevance.get("details"):

                    details = relevance["details"]

                    if details.get("category"):

                        st.write(
                            f"**Category:** "
                            f"{details['category']}"
                        )

                    if details.get("reasoning"):

                        st.write(
                            f"**Reasoning:** "
                            f"{details['reasoning']}"
                        )

                if relevance.get("explanation"):

                    st.write(
                        f"**Explanation:** "
                        f"{relevance['explanation']}"
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # 2. ACCURACY / FACTUALITY JUDGE
                # --------------------------------------------------

                factuality = report["factuality"]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '2. Accuracy / Factuality Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                factuality_score = factuality["score"]

                st.write(
                    f"**Score:** "
                    f"{factuality_score:.2f} / 10"
                    if factuality_score is not None
                    else "**Score:** Unavailable"
                )

                if factuality.get("details"):

                    details = factuality["details"]

                    if details.get("category"):

                        st.write(
                            f"**Category:** "
                            f"{details['category']}"
                        )

                    if details.get("supporting_evidence"):

                        st.write(
                            "**Supporting Evidence:**"
                        )

                        for evidence in details[
                            "supporting_evidence"
                        ]:

                            st.write(
                                f"- {evidence}"
                            )

                if factuality.get("explanation"):

                    st.write(
                        f"**Reasoning:** "
                        f"{factuality['explanation']}"
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # 3. FAITHFULNESS JUDGE
                # --------------------------------------------------

                faithfulness = report["faithfulness"]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '3. Faithfulness Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                faithfulness_score = faithfulness["score"]

                st.write(
                    f"**Score:** "
                    f"{faithfulness_score:.2f} / 10"
                    if faithfulness_score is not None
                    else "**Score:** Uncertain"
                )

                if faithfulness.get("details"):

                    details = faithfulness["details"]

                    if details.get("supported_claims"):

                        st.write(
                            "**Supported Claims:**"
                        )

                        for claim in details[
                            "supported_claims"
                        ]:

                            st.write(
                                f"- {claim}"
                            )

                    if details.get("unsupported_claims"):

                        st.write(
                            "**Unsupported Claims:**"
                        )

                        for claim in details[
                            "unsupported_claims"
                        ]:

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
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # 4. COMPLETENESS JUDGE
                # --------------------------------------------------

                completeness = report["completeness"]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '4. Completeness Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                completeness_score = completeness["score"]

                st.write(
                    f"**Score:** "
                    f"{completeness_score:.2f} / 10"
                    if completeness_score is not None
                    else "**Score:** Unavailable"
                )

                if completeness.get("details"):

                    details = completeness["details"]

                    if details.get(
                        "missing_information"
                    ):

                        st.write(
                            "**Missing Information:**"
                        )

                        for point in details[
                            "missing_information"
                        ]:

                            st.write(
                                f"- {point}"
                            )

                    if details.get("target"):

                        st.write(
                            f"**Evaluation Target:** "
                            f"{details['target']}"
                        )

                if completeness.get("explanation"):

                    st.write(
                        f"**Reasoning:** "
                        f"{completeness['explanation']}"
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # 5. SEMANTIC SIMILARITY JUDGE
                # --------------------------------------------------

                semantic_similarity = report[
                    "semantic_similarity"
                ]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '5. Semantic Similarity Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                semantic_score = semantic_similarity[
                    "score"
                ]

                st.write(
                    f"**Score:** "
                    f"{semantic_score:.2f} / 10"
                    if semantic_score is not None
                    else "**Score:** Unavailable"
                )

                if semantic_similarity.get("details"):

                    details = semantic_similarity[
                        "details"
                    ]

                    if details.get(
                        "similarity"
                    ) is not None:

                        st.write(
                            f"**Similarity:** "
                            f"{details['similarity']}"
                        )

                    if details.get("model"):

                        st.write(
                            f"**Model:** "
                            f"{details['model']}"
                        )

                if semantic_similarity.get(
                    "explanation"
                ):

                    st.write(
                        f"**Reasoning:** "
                        f"{semantic_similarity['explanation']}"
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # 6. HALLUCINATION DETECTION JUDGE
                # --------------------------------------------------

                hallucination = report[
                    "hallucination"
                ]

                st.markdown(
                    '<div class="judge-box">',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="judge-title">'
                    '6. Hallucination Detection Judge'
                    '</div>',
                    unsafe_allow_html=True,
                )

                detected = hallucination[
                    "hallucination_detected"
                ]

                severity = hallucination[
                    "severity"
                ]

                st.write(
                    f"**Hallucination Detected:** "
                    f"{detected}"
                )

                st.write(
                    f"**Severity:** "
                    f"{severity or 'Uncertain'}"
                )

                if hallucination.get(
                    "unsupported_claims"
                ):

                    st.write(
                        "**Unsupported Claims:**"
                    )

                    for claim in hallucination[
                        "unsupported_claims"
                    ]:

                        st.write(
                            f"- {claim}"
                        )

                if hallucination.get(
                    "contradicted_claims"
                ):

                    st.write(
                        "**Contradicted Claims:**"
                    )

                    for claim in hallucination[
                        "contradicted_claims"
                    ]:

                        st.write(
                            f"- {claim}"
                        )

                if hallucination.get(
                    "supported_claims"
                ):

                    st.write(
                        "**Supported Claims:**"
                    )

                    for claim in hallucination[
                        "supported_claims"
                    ]:

                        st.write(
                            f"- {claim}"
                        )

                st.write(
                    f"**Explanation:** "
                    f"{hallucination['explanation']}"
                )

                st.write(
                    f"**Certainty:** "
                    f"{hallucination['certainty']}"
                )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True,
                )


                # --------------------------------------------------
                # FINAL ASSESSMENT
                # --------------------------------------------------

                st.header("Final Assessment")

                st.write(
                    report.get(
                        "final_assessment",
                        "No final assessment available.",
                    )
                )


                # --------------------------------------------------
                # RETRIEVED EVIDENCE
                # --------------------------------------------------

                if report.get("retrieved_context"):

                    st.header("Retrieved Evidence")

                    for index, context in enumerate(
                        report["retrieved_context"],
                        start=1,
                    ):

                        with st.expander(
                            f"Evidence {index}"
                        ):

                            st.write(context)

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
