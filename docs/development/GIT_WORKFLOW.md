# Git Version Control & Branching Strategy

## 1. Branch Hierarchy

```
main (Production / Academic Evaluation Ready)
  ↑
develop (Integration Branch)
  ↑
feature/* (feature/ela-generator, feature/mobilenet-training)
fix/*     (fix/png-transparency-bug)
docs/*    (docs/dataset-guide)
test/*    (test/api-endpoints)
```

- **`main`:** Protected branch. Code here must always pass all unit tests and run without error.
- **`develop`:** Staging branch where completed features are integrated before release.
- **Feature Branches:** Created from `develop` and merged via Pull Request after peer review.

---

## 2. Conventional Commit Standards
All commits must follow the Conventional Commits specification:

```
<type>(<scope>): <concise description in present tense>

[optional detailed body]
[optional issue reference]
```

### Approved Types:
- `feat`: A new user-facing or architectural capability.
- `fix`: A defect or bug resolution.
- `docs`: Documentation updates or additions.
- `refactor`: Code reorganization without functional changes.
- `test`: Adding or correcting pytest unit/integration tests.
- `chore`: Build scripts, dependencies, or configuration adjustments.

### Approved Scopes:
`ela`, `models`, `preprocessing`, `routes`, `dataset`, `services`, `utils`, `config`, `tests`, `docs`

### Examples:
```bash
feat(ela): implement adaptive contrast enhancement in ELAGenerator
fix(preprocessing): handle RGBA transparency by compositing on white background
test(validator): add unit tests for magic-byte spoofing detection
docs(dataset): add CASIA v2 group-aware splitting instructions
```
