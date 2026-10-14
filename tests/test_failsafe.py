import pytest
from google.genai.errors import ClientError

from secondbrain.core.exceptions import GeminiError
from secondbrain.rag.llm import gemini_llm


def _quota_error(retry_delay: str, quota_id: str) -> ClientError:
    return ClientError(429, {"error": {
        "code": 429,
        "message": f"Quota exceeded ({quota_id})",
        "status": "RESOURCE_EXHAUSTED",
        "details": [{"quotaId": quota_id}, {"retryDelay": retry_delay}],
    }})


def test_daily_quota_fails_fast_without_sleeping(monkeypatch):
    def no_sleep(_):
        raise AssertionError("must not sleep on a daily quota")

    monkeypatch.setattr(gemini_llm.time, "sleep", no_sleep)

    def call():
        raise _quota_error("52182s", "GenerateRequestsPerDayPerProjectPerModel-FreeTier")

    with pytest.raises(GeminiError, match="RESOURCE_EXHAUSTED"):
        gemini_llm.execute_with_retry(call)


def test_per_minute_limit_is_retried(monkeypatch):
    slept = []
    monkeypatch.setattr(gemini_llm.time, "sleep", slept.append)
    calls = {"n": 0}

    def call():
        calls["n"] += 1
        if calls["n"] == 1:
            raise _quota_error("20s", "GenerateRequestsPerMinutePerProjectPerModel-FreeTier")
        return "ok"

    assert gemini_llm.execute_with_retry(call) == "ok"
    assert slept == [21.0]
