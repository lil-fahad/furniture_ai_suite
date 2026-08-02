from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from api_utils import allowed_origins, canonical_floor_plan, require_admin, safe_slug


def test_safe_slug_is_stable_and_bounded() -> None:
    assert safe_slug("  Modern Sofa / 2026  ") == "modern-sofa-2026"
    assert safe_slug("***", fallback="furniture") == "furniture"
    assert len(safe_slug("A" * 200)) == 80


def test_canonical_floor_plan_preserves_geometry() -> None:
    raw = {
        "rooms": [
            {
                "id": 7,
                "type": "living_room",
                "bounding_box": {"x": 10, "y": 20, "width": 100, "height": 80},
                "area_pixels": 8000,
                "furniture_recommendations": ["sofa"],
            }
        ],
        "doors": [{"x": 15, "y": 20}],
        "windows": [{"x": 80, "y": 20}],
    }
    result = canonical_floor_plan(raw, width=640, height=480)
    assert result["schema_version"] == "1.0"
    assert result["source_width"] == 640
    assert result["rooms"][0]["id"] == "room-7"
    assert result["rooms"][0]["polygon"][2] == {"x": 110.0, "y": 100.0}
    assert {item["kind"] for item in result["openings"]} == {"door", "window"}
    assert len(result["warnings"]) == 2


def test_wildcard_cors_with_credentials_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("ALLOW_CREDENTIALS", "true")
    with pytest.raises(RuntimeError):
        allowed_origins()


def test_admin_api_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc_info:
        require_admin("candidate")
    assert exc_info.value.status_code == 503


def test_admin_api_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "correct-secret")
    with pytest.raises(HTTPException) as exc_info:
        require_admin("wrong-secret")
    assert exc_info.value.status_code == 401


def test_admin_api_accepts_exact_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "correct-secret")
    assert require_admin("correct-secret") is None


def test_unix_launcher_uses_secure_entrypoint() -> None:
    launcher = Path("run_unix.sh").read_text(encoding="utf-8")
    assert "secure_app:app" in launcher
    assert "safe_api:app" not in launcher
