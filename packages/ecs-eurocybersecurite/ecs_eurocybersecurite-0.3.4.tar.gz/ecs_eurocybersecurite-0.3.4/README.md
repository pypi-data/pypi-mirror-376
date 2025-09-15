
# ECS - Eurocybersecurite Cybersecurity Tools

This project contains cybersecurity and AI tools by Eurocybersecurite.

## Structure du projet

```
ecs_project_v0.3.0/
├── ecs/
│   ├── __init__.py
│   ├── core.py
│   ├── crypto.py
│   ├── audit.py
│   └── ai_tools.py
├── tests/
│   ├── test_core.py
│   ├── test_crypto.py
│   ├── test_audit.py
│   └── test_ai_tools.py
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
└── requirements.txt
```

## Fichiers clés

### ecs/__init__.py
```python
"""ECS - Eurocybersecurite Cybersecurity Tools"""

from .core import greet
from .crypto import hash_text
from .audit import check_log_suspicious
from .ai_tools import classify_text, classify_text_advanced, detect_anomalies_in_logs

__all__ = ["greet", "hash_text", "check_log_suspicious", "classify_text", "classify_text_advanced", "detect_anomalies_in_logs"]
```

### ecs/core.py
```python
def greet(name: str) -> str:
    return f"Hello {name}, welcome to ECS by Eurocybersecurite!"
```

### ecs/crypto.py
```python
import hashlib

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
```

### ecs/audit.py
```python
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
```

### ecs/ai_tools.py
```python
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
```

### tests/test_core.py
```python
from ecs.core import greet

def test_greet():
    assert greet("Mohamed") == "Hello Mohamed, welcome to ECS by Eurocybersecurite!"
```

### tests/test_crypto.py
```python
from ecs.crypto import hash_text
import hashlib

def test_hash_text():
    text = "mypassword"
    assert hash_text(text) == hashlib.sha256(text.encode('utf-8')).hexdigest()
```

### tests/test_audit.py
```python
from ecs.audit import check_log_suspicious

def test_check_log_suspicious(tmp_path):
    log_file = tmp_path / "test.log"
    log_file.write_text("Error: unauthorized access\nAll good\n")
    alerts = check_log_suspicious(str(log_file))
    assert "Error: unauthorized access" in alerts
```

### tests/test_ai_tools.py
```python
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
```

### setup.py
```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='ecs-eurocybersecurite',
    version='0.3.0',
    description='Cybersecurity and AI tools by Eurocybersecurite',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Mohamed Redha Abdessemed',
    author_email='mohamed.abdessemed@eurocybersecurite.fr',
    url='https://github.com/tuteur1/RooR',
    project_urls={
        "Documentation": "https://eurocybersecurite.fr/auth/login.php",
        "Source": "https://github.com/tuteur1/RooR.git",
        "Issues": "https://github.com/tuteur1/RooR/issues",
    },
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "transformers",
        "torch",
        "scikit-learn"
    ],
    entry_points={
        'console_scripts': [
            'ecs-greet=ecs.core:greet',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cybersecurity, AI, tools, python',
    python_requires='>=3.9',
)
```

### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

### requirements.txt
```
flask
transformers
torch
scikit-learn
```

### LICENSE
```
MIT License © Mohamed Redha Abdessemed, Eurocybersecurite
```
