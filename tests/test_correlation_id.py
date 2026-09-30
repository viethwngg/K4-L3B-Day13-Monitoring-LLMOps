from __future__ import annotations

import asyncio
import re
from pathlib import Path

import httpx

from app import logging_config
from app.main import app


def _send(request_id: str | None = None) -> httpx.Response:
    async def send_request() -> httpx.Response:
        headers = {"x-request-id": request_id} if request_id else {}
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/chat",
                headers=headers,
                json={
                    "user_id": "student-01",
                    "session_id": "session-01",
                    "feature": "qa",
                    "message": "Explain observability",
                },
            )

    return asyncio.run(send_request())


def test_valid_request_id_is_propagated(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _send("req-abcdef12")

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-abcdef12"
    assert float(response.headers["x-response-time-ms"]) >= 0
    assert response.json()["correlation_id"] == "req-abcdef12"


def test_invalid_request_id_is_replaced(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logging_config, "LOG_PATH", tmp_path / "logs.jsonl")

    response = _send("unsafe-value")

    generated = response.headers["x-request-id"]
    assert re.fullmatch(r"req-[0-9a-f]{8}", generated)
    assert generated != "unsafe-value"
