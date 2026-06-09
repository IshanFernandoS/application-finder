from __future__ import annotations

import hashlib
import hmac
from datetime import date
from typing import Optional, Tuple


def anonymized_hash(ip: str, user_agent: str, salt: str, day: Optional[date] = None) -> str:
    day = day or date.today()
    message = f"{ip}|{user_agent}|{day.isoformat()}".encode("utf-8")
    key = f"{salt}|{day.isoformat()}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def coarse_user_agent(user_agent: str) -> Tuple[str, str]:
    ua = (user_agent or "").lower()
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        device = "mobile"
    elif "ipad" in ua or "tablet" in ua:
        device = "tablet"
    else:
        device = "desktop"
    if "firefox" in ua:
        browser = "firefox"
    elif "edg" in ua:
        browser = "edge"
    elif "chrome" in ua:
        browser = "chrome"
    elif "safari" in ua:
        browser = "safari"
    else:
        browser = "other"
    return device, browser
