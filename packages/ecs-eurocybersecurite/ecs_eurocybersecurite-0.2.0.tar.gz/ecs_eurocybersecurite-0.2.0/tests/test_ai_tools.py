from ecs.ai_tools import classify_text
def test_classify_text():
    assert classify_text("This is an attack") == "suspicious"
    assert classify_text("All systems normal") == "safe"
