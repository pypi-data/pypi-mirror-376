# Simple rule-based "NLP" engine: match keywords/regex and dispatch intents.
import re
from typing import Tuple, Optional

Intent = Tuple[str, dict]  # (intent_name, params)

INTENT_PATTERNS = [
    # ip intents
    (r"\b(ip|ip address|what(?:'| i)?s my ip|show ip|show my ip)\b", "show_ip"),
    # whoami / user
    (r"\b(who am i|username|whoami)\b", "whoami"),
    # greeting
    (r"\b(hello|hi|hey|greet(?: me)?|say hello(?: to)? (?P<name>\w+))\b", "greet"),
    # date/time
    (r"\b(date|time|what(?:'| i)?s the time|current time|today)\b", "datetime"),
    # ping / check host
    (r"\b(ping|is .* up|check host|check (?:server|host)) (?P<host>[\w\.-]+)\b", "ping_host"),
    # fallback intent
    (r".+", "unknown"),
]


def parse(text: str) -> Intent:
    t = text.strip().lower()
    for pattern, intent in INTENT_PATTERNS:
        m = re.search(pattern, t)
        if m:
            params = m.groupdict() if hasattr(m, "groupdict") else {}
            # normalize host param if exists
            if "host" in params and params["host"]:
                params["host"] = params["host"].strip()
            if "name" in params and params["name"]:
                params["name"] = params["name"].capitalize()
            return intent, params
    return "unknown", {}
