import pandas as pd
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class FakeResponse:
    status_code = 200
    ok = True
    text = ""

    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


def test_single_evaluation_renders_real_scores_and_verdict_chart():
    user = {"id": 1, "full_name": "Chart User"}
    dashboard = {
        "total_evaluations": 0,
        "pass_count": 0,
        "needs_improvement_count": 0,
        "fail_count": 0,
        "evaluations": [],
    }
    evaluation = {
        "relevance": {"score": 8.5},
        "factuality": {"score": 7.0},
        "completeness": {"score": 9.0},
        "hallucination": {
            "hallucination_detected": False,
            "certainty": "certain",
        },
        "verdict": "PASS",
        "overall_score": 8.1,
        "verdict_overall_score": 8.1,
    }

    def fake_get(url, **kwargs):
        return FakeResponse(user if url.endswith("/auth/me") else dashboard)

    with patch("requests.get", side_effect=fake_get), patch(
        "requests.post", return_value=FakeResponse(evaluation)
    ):
        app = AppTest.from_file("frontend/app.py", default_timeout=30)
        app.session_state["auth_token"] = "valid-test-token"
        app.run()
        app.radio[0].set_value(app.radio[0].options[1]).run()
        for field, value in zip(app.text_area, ["Question", "Response", "", ""]):
            field.set_value(value)
        next(button for button in app.button if "Evaluate Response" in button.label).click().run()

    assert not app.exception
    charts = app.get("arrow_vega_lite_chart")
    assert len(charts) == 1
    assert ("Evaluation verdict", "PASS") in [
        (metric.label, metric.value) for metric in app.metric
    ]
    assert ("Hallucination classification", "Not detected") in [
        (metric.label, metric.value) for metric in app.metric
    ]


def test_batch_results_render_score_verdict_and_average_charts():
    user = {"id": 2, "full_name": "Batch Chart User"}
    results = pd.DataFrame(
        [
            {
                "Record": 1,
                "Question": "First question",
                "AI Response": "First answer",
                "Relevance": 8.0,
                "Factuality": 7.0,
                "Completeness": 9.0,
                "Hallucination": "Not detected",
                "Verdict": "PASS",
            },
            {
                "Record": 2,
                "Question": "Second question",
                "AI Response": "Second answer",
                "Relevance": 4.0,
                "Factuality": None,
                "Completeness": 5.0,
                "Hallucination": "Uncertain",
                "Verdict": "FAIL",
            },
        ]
    )

    with patch("requests.get", return_value=FakeResponse(user)):
        app = AppTest.from_file("frontend/app.py", default_timeout=30)
        app.session_state["auth_token"] = "valid-test-token"
        app.session_state["batch_results"] = results
        app.run()
        app.radio[0].set_value(app.radio[0].options[3]).run()

    assert not app.exception
    assert len(app.get("arrow_vega_lite_chart")) == 3
    assert "Batch score comparison" in [item.value for item in app.subheader]
    assert "Verdict counts" in [item.value for item in app.subheader]
    assert "Average evaluation scores" in [item.value for item in app.subheader]
