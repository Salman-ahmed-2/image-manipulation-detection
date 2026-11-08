# Label Mapping & Classification Schema

## 1. Binary Classification Schema
The detection pipeline maps all input imagery into a strict binary classification scheme:

| Class Integer | Categorical Name | Description | Probability Interval |
| :---: | :--- | :--- | :---: |
| `0` | **Authentic** | Pristine, unmodified natural photograph | $P < 0.5$ |
| `1` | **Manipulated** | Digitally tampered photograph (Copy-Move or Splicing) | $P \ge 0.5$ |

---

## 2. Filename-to-Label Extraction Rules

In both CASIA v1.0 and CASIA v2.0, class identity is encoded directly into filename prefixes:

| Dataset | Filename Pattern | Assigned Label | Manipulation Type | Example Filename |
| :--- | :--- | :---: | :--- | :--- |
| **CASIA v1** | `Au_<cat>_<id>.jpg` | `0` (Authentic) | Pristine | `Au_ani_0001.jpg` |
| **CASIA v1** | `Sp_<cat>_<id>.jpg` or `Tp_<id>.jpg` | `1` (Manipulated) | Splicing | `Sp_ani_0001.jpg` |
| **CASIA v2** | `Au_<cat>_<id>.jpg` | `0` (Authentic) | Pristine | `Au_ani_00001.jpg` |
| **CASIA v2** | `Tp_S_<donor>_<target>_<id>.jpg` | `1` (Manipulated) | Copy-Move (Same image) | `Tp_S_CRN_M_N_nat10129_nat10129_00123.jpg` |
| **CASIA v2** | `Tp_D_<donor>_<target>_<id>.jpg` | `1` (Manipulated) | Splicing (Different images) | `Tp_D_CRN_S_N_ani00073_ani00068_00192.jpg` |

---

## 3. Label Extraction Logic (Python Reference)

```python
from pathlib import Path
from typing import Tuple

def extract_label_from_filename(filename: str) -> Tuple[int, str, str]:
    """Extract binary label, label name, and manipulation type from filename.
    
    Args:
        filename: Name of the CASIA image file (e.g. 'Au_ani_0001.jpg').
        
    Returns:
        Tuple of (label_int, label_name, manipulation_type).
        
    Raises:
        ValueError: If filename does not match known CASIA naming conventions.
    """
    stem = Path(filename).name
    
    if stem.startswith("Au_"):
        return (0, "Authentic", "Pristine")
    elif stem.startswith("Tp_S_"):
        return (1, "Manipulated", "Copy-Move")
    elif stem.startswith("Tp_D_") or stem.startswith("Sp_"):
        return (1, "Manipulated", "Splicing")
    elif stem.startswith("Tp_"):
        return (1, "Manipulated", "General-Tampered")
    else:
        raise ValueError(f"Unrecognized filename format: {filename}")
```

---

## 4. Metadata CSV Schemas

### `data/metadata/dataset_labels.csv`
Columns:
- `image_id` (str): Unique hash or standardized sequential identifier.
- `filename` (str): Original filename.
- `dataset_version` (str): "CASIA_v1" or "CASIA_v2".
- `label` (int): 0 or 1.
- `label_name` (str): "Authentic" or "Manipulated".
- `manipulation_type` (str): "Pristine", "Copy-Move", or "Splicing".
- `has_ground_truth_mask` (bool): True if matching binary mask exists in `data/annotations/`.
- `mask_filename` (str): Corresponding mask filename if available.
