# Dummy AI tools for ECS

def classify_text(text: str) -> str:
    suspicious_keywords = ["attack", "breach", "malware", "unauthorized"]
    return "suspicious" if any(word in text.lower() for word in suspicious_keywords) else "safe"

def classify_text_advanced(text: str) -> str:
    # Placeholder for NLP model
    return classify_text(text)

def detect_anomalies_in_logs(file_path: str):
    alerts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if any(word in line.lower() for word in ["error", "failed", "unauthorized", "attack"]):
                    alerts.append(line.strip())
    except FileNotFoundError:
        alerts.append(f"File not found: {file_path}")
    return alerts
