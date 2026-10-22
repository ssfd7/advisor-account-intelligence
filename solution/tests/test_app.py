"""Screen 1 runs all four beats without errors, in replay mode (no API call), and the final search finds both advisors."""
import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def test_screen_one_runs_every_beat():
    at = AppTest.from_file("../app.py", default_timeout=180)
    at.query_params["replay"] = "1"
    at.run()
    for _ in range(3):
        at.button[0].click().run()
        assert not at.exception, [e.message for e in at.exception]
    advisors = set(at.dataframe[0].value["Advisor"])
    assert advisors == {"Maya Chen", "May Chen"}
