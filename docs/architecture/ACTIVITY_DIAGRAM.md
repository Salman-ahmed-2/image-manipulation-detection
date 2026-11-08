# Activity Diagrams

## 1. Primary User Journey Activity Diagram
This diagram models the entire operational lifecycle from the moment a user accesses the web application through to report download and session disposal.

```mermaid
flowchart TD
    Start(["User Opens Application Browser"]) --> ViewHome["Display Home Page (/) with Drop-Zone"]
    ViewHome --> SelectFile["User Selects Local File (JPG/PNG)"]
    SelectFile --> ClientVal{"Client-Side File Check"}
    ClientVal -->|Invalid Extension or > 16MB| AlertClient["Display Instant Browser Alert"]
    AlertClient --> SelectFile
    ClientVal -->|Passed| ShowPreview["Render Local Image Preview"]
    ShowPreview --> ChooseModel{"Model Selected?"}
    ChooseModel -->|Default| SetMobileNet["Select MobileNetV2"]
    ChooseModel -->|Explicit Option| SetCNN["Select Custom CNN"]
    SetMobileNet --> ClickSubmit["User Clicks 'Analyze Image'"]
    SetCNN --> ClickSubmit
    ClickSubmit --> ShowSpinner["Show Loading Spinner Animation"]
    ShowSpinner --> SendRequest["Dispatch POST /analyze Multipart Payload"]
    SendRequest --> ServerVal{"Server-Side Validation"}
    ServerVal -->|Failed Check| RenderError["Render Error View (error.html) with HTTP 400/413"]
    RenderError --> EndErr(["User Returns Home"])
    
    ServerVal -->|Passed| SaveTemp["Save Image to temp/uploads/<session_id>/"]
    SaveTemp --> ParallelFork["Fork Parallel Pipeline"]
    
    ParallelFork --> Preprocess["Preprocess Tensor (224x224x3, Normalized)"]
    Preprocess --> ModelInference["Execute Forward Pass (Sigmoid Probability)"]
    ModelInference --> ComputeConfidence["Compute Verdict & Confidence Score"]
    
    ParallelFork --> GenELA["Generate ELA Recompression Residual (Q=90, 10x Scale)"]
    GenELA --> SaveELA["Save ELA Output (PNG) to Session Directory"]
    
    ComputeConfidence --> ParallelJoin["Join Results"]
    SaveELA --> ParallelJoin
    
    ParallelJoin --> RenderDashboard["Render Result Dashboard (result.html)"]
    RenderDashboard --> ReviewResult["User Inspects Side-by-Side Images & Metrics"]
    ReviewResult --> DownloadChoice{"User Requests PDF Report?"}
    
    DownloadChoice -->|Yes| ReqPDF["Dispatch GET /report/<session_id>"]
    ReqPDF --> BuildPDF["Compile PDF Document via ReportService"]
    BuildPDF --> StreamPDF["Download Attachment to Browser"]
    StreamPDF --> CleanupFiles["Trigger Session Directory Deletion"]
    
    DownloadChoice -->|No / Navigates Away| TimeoutCleanup["Scheduled Sweep Deletes Files (> 30 Min)"]
    CleanupFiles --> Done(["Session Successfully Terminated"])
    TimeoutCleanup --> Done
```

---

## 2. ELA Generation Activity Detail

```mermaid
flowchart TD
    ELAStart(["Start ELA Generation"]) --> IngestImage["Ingest Source Image File"]
    IngestImage --> ModeCheck{"Is Mode RGB?"}
    ModeCheck -->|No (RGBA/Grayscale)| ConvertRGB["Convert to Standard 3-Channel RGB"]
    ModeCheck -->|Yes| FormatCheck{"Original Format PNG?"}
    ConvertRGB --> FormatCheck
    FormatCheck -->|Yes| LogPNGNotice["Log Forensic Notice: ELA on PNG introduces compression baseline"]
    FormatCheck -->|No| EncodeJPEG["Encode to In-Memory Bytes at JPEG Quality = 90"]
    LogPNGNotice --> EncodeJPEG
    EncodeJPEG --> DecodeJPEG["Decode Recompressed JPEG into Pillow Object"]
    DecodeJPEG --> PixelDiff["Compute Pixel-wise Difference: abs(Original - Recompressed)"]
    PixelDiff --> Scale10x["Multiply Pixel Residues by Enhancement Factor (10x)"]
    Scale10x --> ClipBoundaries["Clip Values to uint8 [0, 255] Range"]
    ClipBoundaries --> OutputPNG["Save High-Contrast ELA Map as PNG"]
    OutputPNG --> ELAEnd(["Return ELA File Path"])
```
