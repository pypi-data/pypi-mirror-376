from ecs.ai_tools import classify_text, classify_text_advanced, detect_anomalies_in_logs

def test_classify_text():
    assert classify_text("This is an attack") == "suspicious"
    assert classify_text("All systems normal") == "safe"

def test_classify_text_advanced():
    assert classify_text_advanced("This is an attack") == "suspicious"

def test_detect_anomalies_in_logs(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("Error: unauthorized access\nAll good\n")
    anomalies = detect_anomalies_in_logs(str(log_file))
    assert "Error: unauthorized access" in anomalies
