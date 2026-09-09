import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="LLM Evaluation System", page_icon="E")
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fb;
    }

    h1 {
        color: #1f4e79;
        text-align: center;
    }

    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    [data-testid="stMetricValue"] {
        color: #1f4e79;
        font-weight: bold;
    }

    [data-testid="stMetricLabel"] {
        color: #444444;
    }

    .stButton > button {
        background-color: #1f4e79;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #163a5c;
        color: white;
    }

    .stTextArea textarea {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)
st.title("Automated LLM Evaluation and Hallucination Detection System")
st.caption("Deterministic baseline evaluation with optional local knowledge-base retrieval.")

question = st.text_area("Question", height=120)
response = st.text_area("AI Response", height=160)
reference_answer = st.text_area("Reference Answer (optional)", height=120)
source_document = st.text_area("Source Document / Context (optional)", height=160)
use_knowledge_base = st.checkbox("Use Knowledge Base for Retrieval")
top_k = st.number_input("Retrieved chunks", min_value=1, max_value=20, value=5, step=1)

if st.button("Evaluate Response", type="primary"):
	if not question.strip() or not response.strip():
		st.error("Please enter both a question and an AI response.")
	else:
		payload = {
			"question": question,
			"response": response,
			"reference_answer": reference_answer or None,
			"source_document": source_document or None,
			"use_knowledge_base": use_knowledge_base,
			"top_k": top_k,
		}
		try:
			result = requests.post(f"{BACKEND_URL}/evaluate", json=payload, timeout=60)
			result.raise_for_status()
			report = result.json()
			overall = report["overall_score"]
			st.metric("Overall Score", f"{overall:.2f} / 10" if overall is not None else "Unavailable")
			columns = st.columns(5)
			for column, name in zip(columns, ("relevance", "factuality", "faithfulness", "completeness", "semantic_similarity")):
				score = report[name]["score"]
				column.metric(name.replace("_", " ").title(), f"{score:.2f} / 10" if score is not None else "Unavailable")
			st.subheader("Hallucination")
			hallucination = report["hallucination"]
			st.write(f"Detected: {hallucination['hallucination_detected']}")
			st.write(f"Severity: {hallucination['severity'] or 'Uncertain'}")
			st.write(hallucination["explanation"])
			st.subheader("Final Assessment")
			st.write(report["final_assessment"])
			st.subheader("Retrieved Evidence")
			if report["retrieved_context"]:
				for index, context in enumerate(report["retrieved_context"], start=1):
					st.write(f"{index}. {context}")
			else:
				st.info("No retrieved context was used.")
		except requests.exceptions.RequestException:
			st.error("Could not contact the FastAPI backend. Start it with uvicorn first.")
		except (KeyError, ValueError):
			st.error("The backend returned an invalid evaluation result.")
