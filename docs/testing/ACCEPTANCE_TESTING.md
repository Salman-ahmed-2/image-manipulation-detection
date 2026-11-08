# User Acceptance Testing (UAT) & Manual Verification Matrix

## 1. Acceptance Testing Protocol
User Acceptance Testing ensures that all user-facing interactions, visual elements, validation guards, and forensic disclaimers behave reliably in real-world scenarios.

---

## 2. UAT Test Execution Matrix

| Test ID | Test Scenario | Input / Action | Expected Result | Verification Status |
| :---: | :--- | :--- | :--- | :---: |
| **UAT-01** | Pristine JPEG Upload | Upload natural unaltered `.jpg` photo (2.1 MB) | Result badge shows "Authentic", confidence displayed, ELA map shows uniform dark/gray texture | [PENDING VERIFICATION] |
| **UAT-02** | Spliced Image Upload | Upload verified CASIA spliced image (`Tp_D_...`) | Result badge shows "Potentially Manipulated", ELA map highlights foreign object boundaries | [PENDING VERIFICATION] |
| **UAT-03** | Unsupported File Rejection | Attempt to upload `.pdf` or `.docx` file | Client alert appears immediately; submission blocked | [PENDING VERIFICATION] |
| **UAT-04** | Magic-Byte Spoofing Defense | Upload executable renamed to `sample.jpg` | Server returns HTTP 400 Bad Request with error explanation | [PENDING VERIFICATION] |
| **UAT-05** | Oversized Payload Rejection | Upload image larger than 16 MB | HTTP 413 Payload Too Large rendered with guidance | [PENDING VERIFICATION] |
| **UAT-06** | PDF Report Generation | Click "Download PDF Report" on results page | Multi-page PDF downloads immediately with photos & disclaimer | [PENDING VERIFICATION] |
| **UAT-07** | Ephemeral File Cleanup | Wait 30 minutes after analysis | Temp session directory purged automatically from disk | [PENDING VERIFICATION] |
| **UAT-08** | Mobile Viewport Usability | Access site on 375px mobile screen (Chrome devtools) | UI stacks cleanly, no horizontal scrolling, upload works | [PENDING VERIFICATION] |
