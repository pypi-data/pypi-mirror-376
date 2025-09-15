def classify_text(text: str) -> str:
    suspicious_keywords = ["attack", "breach", "malware", "unauthorized"]
    if any(word in text.lower() for word in suspicious_keywords):
        return "suspicious"
    return "safe"
