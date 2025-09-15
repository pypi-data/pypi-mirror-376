def check_log_suspicious(file_path: str):
    suspicious_keywords = ["error", "failed", "unauthorized", "warning"]
    alerts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if any(keyword in line.lower() for keyword in suspicious_keywords):
                    alerts.append(line.strip())
    except FileNotFoundError:
        alerts.append(f"File not found: {file_path}")
    return alerts
