"""Tiny, dependency-free user-agent parser — enough for a device label."""
from __future__ import annotations


def parse_user_agent(ua: str) -> tuple[str, str, str]:
    """Return (browser, os, friendly_label) from a user-agent string."""
    if not ua:
        return "Unknown", "Unknown", "Unknown device"
    u = ua.lower()

    # Order matters: Edge/Chrome share tokens, so check the more specific first.
    if "edg/" in u or "edge" in u:
        browser = "Edge"
    elif "opr/" in u or "opera" in u:
        browser = "Opera"
    elif "firefox" in u:
        browser = "Firefox"
    elif "chrome" in u and "chromium" not in u:
        browser = "Chrome"
    elif "safari" in u:
        browser = "Safari"
    else:
        browser = "Browser"

    if "windows" in u:
        os_name = "Windows"
    elif "android" in u:
        os_name = "Android"
    elif "iphone" in u or "ipad" in u or "ios" in u:
        os_name = "iOS"
    elif "mac os" in u or "macintosh" in u:
        os_name = "macOS"
    elif "linux" in u:
        os_name = "Linux"
    else:
        os_name = "Unknown OS"

    is_mobile = any(t in u for t in ("mobile", "android", "iphone", "ipad"))
    kind = "Mobile" if is_mobile else "Desktop"
    label = f"{kind} · {browser} on {os_name}"
    return browser, os_name, label
