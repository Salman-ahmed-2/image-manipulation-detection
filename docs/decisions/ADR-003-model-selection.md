# ADR-003: Deep Learning Model Architecture Selection

## Context & Problem Statement
The project requires building a binary classification model (Authentic vs. Potentially Manipulated). To provide academic rigor and research value, the team must determine whether to train a neural network from scratch or leverage transfer learning from a general-purpose vision backbone.

## Considered Options
1. **Custom 4-Block CNN vs. MobileNetV2 Dual Architecture Study** (Selected)
2. **ResNet50 / VGG16 Transfer Learning Only** (Rejected: Heavy parameter footprint, slow inference on CPU)
3. **Vision Transformer (ViT) from Scratch** (Rejected: Requires massive training data, prone to severe overfitting on small datasets)
4. **Custom CNN Exclusively** (Rejected: Misses opportunity to evaluate transfer learning utility in image forensics)

## Decision Outcome
**Chosen Option:** **Option 1: Custom 4-Block CNN vs. MobileNetV2 Dual Architecture Study**

### Positive Consequences:
- **Research Rigor:** Enables an empirical comparative study contrasting features learned from scratch against pre-trained ImageNet representations.
- **Compute Feasibility:** Both models train comfortably on Google Colab T4 GPUs within reasonable time frames (< 2 hours per training run).
- **Inference Efficiency:** MobileNetV2 features inverted residual bottlenecks and depthwise separable convolutions, guaranteeing $< 100\text{ ms}$ inference on standard CPUs.

### Negative Consequences:
- Managing and evaluating two separate training pipelines doubles the experiment logging overhead.

## Status
**ACCEPTED** (2026-11-08)
