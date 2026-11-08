# Development Environment Configuration

## 1. Local IDE Recommendations (VS Code)

### Recommended Extensions:
- `ms-python.python`: Python language support, IntelliSense, and debugging.
- `ms-python.vscode-pylance`: Fast static type analysis.
- `charliermarsh.ruff`: High-speed linting and code formatting.
- `bierner.markdown-mermaid`: Live preview for Mermaid architectural diagrams.

### Workspace Configuration (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.testing.pytestArgs": ["tests"],
  "python.testing.unittestEnabled": false,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "python.formatting.provider": "none",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll": "explicit",
      "source.organizeImports": "explicit"
    }
  }
}
```

---

## 2. Google Colab GPU Environment Setup for Model Training
When training models on CASIA v2.0 without a local GPU, Google Colab provides free T4 GPU runtimes.

### Recommended Notebook Header Cell:
```python
# 1. Mount Google Drive for persistent artifact checkpointing
from google.colab import drive
drive.mount('/content/drive')

# 2. Clone repository or link project folder
import os
os.chdir('/content/drive/MyDrive/image-manipulation-detection')

# 3. Verify CUDA GPU availability
import tensorflow as tf
print("TensorFlow Version:", tf.__version__)
print("GPU Available:", tf.config.list_physical_devices('GPU'))
assert len(tf.config.list_physical_devices('GPU')) > 0, "No GPU detected! Change runtime type."
```
