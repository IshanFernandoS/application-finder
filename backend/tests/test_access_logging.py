from datetime import date

from backend.app.analytics.anonymize import anonymized_hash, coarse_user_agent


def test_access_hash_does_not_expose_raw_ip():
    hashed = anonymized_hash("192.0.2.1", "Mozilla/5.0", "salt", day=date(2026, 6, 9))
    assert "192.0.2.1" not in hashed
    assert len(hashed) == 64


def test_coarse_user_agent_drops_raw_string():
    device, browser = coarse_user_agent("Mozilla/5.0 Chrome Mobile")
    assert device == "mobile"
    assert browser == "chrome"
