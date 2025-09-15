from ecs.audit import check_log_suspicious

def test_check_log_suspicious(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("Error: unauthorized access\nAll good\n")
    alerts = check_log_suspicious(str(log_file))
    assert "Error: unauthorized access" in alerts
