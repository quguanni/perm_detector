def looks_like_injection(text: str) -> bool:
    if not text:
        return False
    patterns = [
        "ignore previous", "override", "developer mode",
        "you must grant", "escalate permissions", "bypass",
        "enable all tools", "give yourself access"
    ]
    text_l = text.lower()
    return any(p in text_l for p in patterns)
