# Installation & Local Setup Guide

## 1. System Requirements
- **Operating System:** Linux (Ubuntu 22.04+ LTS recommended), macOS (12+), or Windows 11 with WSL2.
- **Python Version:** Python 3.11.x (CPython 64-bit).
- **RAM:** 8 GB minimum (16 GB recommended for dataset preparation).
- **Disk Space:** 5 GB free disk space (excluding raw CASIA image archives).

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-team/image-manipulation-detection.git
cd image-manipulation-detection
```

### Step 2: Initialize Python 3.11 Virtual Environment
```bash
python3.11 -m venv venv

# On Linux/macOS:
source venv/bin/activate

# On Windows (cmd):
venv\Scripts\activate.bat

# On Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Step 3: Upgrade Package Manager & Install Dependencies
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Ensure `.env` contains:
```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-replace-in-production-32-chars
PORT=5000
```

### Step 5: Verify Directory Tree
Ensure all artifact and temporary directories exist:
```bash
mkdir -p artifacts/models artifacts/plots artifacts/predictions artifacts/reports temp/uploads
```

### Step 6: Execute Health Checks & Tests
```bash
pytest tests/ -v
```

### Step 7: Launch Development Server
```bash
python run.py
# Server will start on http://127.0.0.1:5000
```
