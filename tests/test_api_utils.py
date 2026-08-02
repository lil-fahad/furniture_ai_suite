from __future__ import annotations

import pytest

from api_utils import allowed_origins, canonical_floor_plan, safe_slug


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


def test_wildcard_cors_with_credentials_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("ALLOW_CREDENTIALS", "true")
    with pytest.raises(RuntimeError):
        allowed_origins()
