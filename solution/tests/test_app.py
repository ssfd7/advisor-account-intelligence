"""Screen 1 runs every step without errors in replay mode (no API call); steps unlock only after the work before them;
the search finds both advisors; going back hides later state; the business case computes."""
import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest


def test_screen_one_steps_unlock_in_order_and_run():
    at = AppTest.from_file("../app.py", default_timeout=180)
    at.query_params["replay"] = "1"
    at.run()
    for i in range(1, 5):
        at.button(key=f"step{i}").click().run()
        assert not at.exception, [e.message for e in at.exception]
        if i == 3:
            assert set(at.dataframe[0].value["Advisor"]) == {"Maya Chen", "May Chen"}
    assert any("year-one ROI" in m.value for m in at.markdown)
    at.button(key="step1").click().run()
    assert not at.exception and not any("Don't say" in m.value for m in at.markdown)


def test_later_steps_start_locked():
    at = AppTest.from_file("../app.py", default_timeout=60)
    at.query_params["replay"] = "1"
    at.run()
    assert [at.button(key=f"step{i}").disabled for i in range(5)] == [False, False, True, True, True]
