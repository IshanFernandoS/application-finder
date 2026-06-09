from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


def get_json(url: str, params: Dict[str, object], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    encoded = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    request = urllib.request.Request(url + ("?" + encoded if encoded else ""), headers=headers or {})
    with urllib.request.urlopen(request, timeout=25) as response:  # nosec - caller controls public API URLs
        return json.loads(response.read().decode("utf-8"))
