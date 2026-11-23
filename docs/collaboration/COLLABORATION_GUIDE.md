# Three-Person Collaboration Guide

**Image Manipulation Detection System**

This guide defines team responsibilities, Git workflow, and coordination
protocols for the three-person project team.

---

## Team Structure and Responsibilities

### Member 1 — Training Manager

**Primary responsibilities:**
- Configure and manage Google Colab sessions
- Run MobileNetV2 training (`02_mobilenetv2_training.ipynb`)
- Monitor GPU usage and training progress
- Save training checkpoints and prevent session loss
- Download and version-tag trained model artifacts
- Share `mobilenetv2.keras` and config JSON files with the team

**Git ownership:**
- `notebooks/colab/02_mobilenetv2_training.ipynb`
- `artifacts/models/model_config.json`
- `artifacts/models/preprocessing_config.json`
- `src/training/` modules (if modifications are needed)

---

### Member 2 — Dataset Manager

**Primary responsibilities:**
- Obtain and organize CASIA v1.0 and v2.0 image datasets
- Run dataset preparation (`01_dataset_preparation.ipynb`)
- Validate image integrity and label correctness
- Maintain the authoritative `dataset_split.csv`
- Ensure all teammates use the same split file
- Document dataset statistics and any anomalies

**Git ownership:**
- `notebooks/colab/01_dataset_preparation.ipynb`
- `data/metadata/` CSV and JSON files
- `src/data/` modules (if modifications are needed)
- `docs/dataset/` documentation

---

### Member 3 — Evaluation and Application Integration

**Primary responsibilities:**
- Run model evaluation (`03_mobilenetv2_evaluation.ipynb`)
- Verify prediction quality and sanity-check results
- Integrate the trained `mobilenetv2.keras` into the Flask app
- Test the complete upload → ELA → prediction → display workflow
- Report bugs and performance issues to the team

**Git ownership:**
- `notebooks/colab/03_mobilenetv2_evaluation.ipynb`
- `artifacts/models/evaluation_results.json`
- `web/routes/`, `web/templates/`, `web/static/`
- `tests/` test files
- `docs/application/` documentation

---

## Git Workflow

### Branch Naming Convention

```
feature/<short-description>   # New features
fix/<short-description>        # Bug fixes
docs/<short-description>       # Documentation updates
refactor/<short-description>   # Code refactoring
test/<short-description>       # Test additions
```

**Examples:**
```
feature/mobilenet-training-notebook
fix/detection-service-preprocessing
docs/colab-guide-update
test/model-loader-unit-tests
```

### Never Commit Directly to `main`

All changes to `main` must go through a pull request reviewed by **at least one
other teammate**.

```bash
# Correct workflow
git checkout -b feature/my-feature
# ... make changes ...
git add <files>
git commit -m "feat(training): add phase2 fine-tuning callbacks"
git push origin feature/my-feature
# Open a Pull Request on GitHub
```

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <short description>

[optional body]
[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`

**Scopes:** `ela`, `models`, `preprocessing`, `routes`, `training`, `dataset`,
`config`, `tests`, `docs`, `notebooks`

**Examples:**
```
feat(notebooks): add checkpoint recovery cell to training notebook
fix(detection-service): correct preprocessing mode comparison
docs(colab): add GPU runtime setup instructions
test(model-loader): add fallback mock model assertion
```

### Delete Feature Branches After Merging

```bash
# After PR is merged on GitHub
git checkout main
git pull origin main
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

---

## Shared Dataset Split Requirement

**All teammates must use the same `dataset_split.csv`.**

The authoritative split is created by Member 2 (Dataset Manager) and committed
to `data/metadata/dataset_split.csv`. **Never regenerate the split independently**
— doing so will produce different random assignments and invalidate cross-member comparisons.

### How to Share the Split

1. Member 2 runs `01_dataset_preparation.ipynb` on the full CASIA dataset
2. Member 2 commits and pushes `data/metadata/dataset_split.csv`
3. All members pull the latest `main` before running any training or evaluation

```bash
git pull origin main
# Confirm split exists
ls data/metadata/dataset_split.csv
```

---

## Training Session Coordination

### One Active Training Session at a Time

Do not run multiple Colab training sessions simultaneously on the same runtime.
Two sessions sharing the same checkpoint directory will overwrite each other's
files.

**Before starting training:**
1. Confirm on your team chat that no other session is running
2. Check that you have the latest `dataset_split.csv` from `main`
3. Set `GITHUB_REPO_URL` and `REPO_NAME` to the shared repository

### After Training Completes

1. Download `mobilenetv2.keras`, `model_config.json`, and `evaluation_results.json`
2. Share them with teammates via a file-sharing method agreed by the team
3. Commit the JSON config files to GitHub (they are small enough)
4. Do NOT commit `mobilenetv2.keras` to GitHub (it is in `.gitignore`)

---

## Code Review Checklist

Before approving a pull request, verify:

- [ ] Code follows PEP 8 (max 100 chars per line, 4-space indent)
- [ ] All public functions have Google-style docstrings with type hints
- [ ] No hardcoded paths or magic numbers — all constants in `config.py`
- [ ] No bare `except:` clauses
- [ ] `print()` is not used in production code — `logger.*` is used instead
- [ ] No duplicate functions (search before creating new ones)
- [ ] No model training logic in Flask routes or services
- [ ] `pytest tests/` passes with no failures
- [ ] No CASIA image files or `.keras` model files committed

---

## Communication Protocol

| Event | Action |
|-------|--------|
| Starting a Colab training run | Notify team in group chat |
| Training completes | Share model file + evaluation summary |
| New `dataset_split.csv` committed | Notify all members to pull before training |
| A test fails | Open a GitHub issue describing the failure |
| Flask integration bug found | Open a GitHub issue, assign to Member 3 |
| Merge conflict | Resolve locally, never force-push to `main` |

---

## Preventing Common Mistakes

| Mistake | Prevention |
|---------|-----------|
| Two members regenerating splits | Only Member 2 runs Notebook 1 on the full dataset |
| Committing `.keras` model files | Covered by `.gitignore` |
| Committing CASIA images | Covered by `.gitignore` |
| Running training locally | Training runs in Colab only |
| Using test data for model selection | Notebook 2 uses validation; Notebook 3 uses test |
| Hardcoding paths | All paths derived from `Config.*` constants |
