from __future__ import annotations

BASE_URL = "https://api.tessera.test"
API_KEY = "tsk_test_key"


def problem_json(status: int, *, title: str, detail: str | None = None) -> dict[str, object]:
    body: dict[str, object] = {"status": status, "title": title, "type": "about:blank"}
    if detail is not None:
        body["detail"] = detail
    return body
