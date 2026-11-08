# Core Source Code Package (`src/`)

This directory houses the authoritative backend business logic, neural network architectures, data processing pipelines, image forensics algorithms, and system utilities.

## Module Structure & Responsibilities

```
src/
├── data/               # Ingestion, validation, group-aware splitting, augmentation
│   ├── augmentation.py      # Spatial transforms preserving compression artifacts
│   ├── dataset_loader.py    # Batched dataset loading and streaming
│   ├── dataset_splitter.py  # Group-aware train/val/test partitioning
│   └── dataset_validator.py # Header integrity and corruption filtering
│
├── evaluation/         # Metrics and performance evaluation
│   ├── confusion_matrix.py  # Confusion matrix generation and heatmap plots
│   ├── metrics.py           # Accuracy, Precision, Recall, F1, ROC-AUC
│   └── visualization.py     # Training history and loss/accuracy curves
│
├── explainability/     # Optional visual interpretability
│   └── gradcam.py           # Gradient-weighted Class Activation Mapping
│
├── models/             # Neural network architectures and inference engine
│   ├── cnn_model.py         # 4-block Custom CNN definition
│   ├── mobilenet_model.py   # MobileNetV2 transfer learning architecture
│   ├── model_loader.py      # Thread-safe in-memory model cache
│   └── predictor.py         # Forward pass and probability scoring
│
├── preprocessing/      # Image manipulation and forensic processing
│   ├── ela_generator.py     # Error Level Analysis recompression engine
│   ├── image_loader.py      # RGB loading and colorspace normalization
│   ├── image_normalizer.py  # Tensor value scaling ([0,1] or [-1,1])
│   └── image_resizer.py     # Standardized bicubic 224x224 resizing
│
├── services/           # Orchestrated application business logic
│   ├── detection_service.py # End-to-end analysis coordination
│   ├── ela_service.py       # ELA rendering and caching service
│   └── report_service.py    # PDF report compilation via fpdf2
│
├── training/           # Model training and optimization loops
│   ├── callbacks.py         # EarlyStopping, Checkpoint, ReduceLROnPlateau
│   ├── evaluate.py          # Model testing against held-out test split
│   ├── train_cnn.py         # Custom CNN training script
│   └── train_mobilenet.py   # MobileNetV2 two-stage fine-tuning script
│
└── utils/              # Cross-cutting system utilities
    ├── exceptions.py        # Domain exception hierarchy
    ├── file_validator.py    # Magic bytes, extension, and size validation
    ├── image_utils.py       # Array conversion and byte buffer utilities
    └── logger.py            # Centralized logging configuration
```

## Architectural Invariants
1. **No Web Imports:** Modules under `src/` must never import from `web/`.
2. **Decoupled Route Handlers:** Web routes must never invoke `src/models/` directly; all execution passes through `src/services/`.
3. **No Hardcoded Constants:** All hyperparameters, paths, and thresholds must be imported from `config.py`.
