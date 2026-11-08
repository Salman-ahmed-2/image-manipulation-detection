# ADR-004: Monolithic Service Architecture & Ephemeral State Management

## Context & Problem Statement
The team must establish an architectural design for the web application layer that balances simplicity, high inference performance, user data confidentiality, and clean separation of concerns.

## Considered Options
1. **Modular Monolith with Service Layer & Ephemeral File Session Storage** (Selected)
2. **Microservices with Asynchronous Message Queue (Flask + Celery + Redis + PostgreSQL)** (Rejected: Extreme complexity for a university semester project)
3. **Single Flat Flask Script without Service Layer** (Rejected: Tight coupling, untestable, unmaintainable)

## Decision Outcome
**Chosen Option:** **Option 1: Modular Monolith with Service Layer & Ephemeral File Session Storage**

### Key Design Tenets:
1. **Decoupled Service Layer:** Business logic resides entirely within `src/services/` (`detection_service.py`, `ela_service.py`, `report_service.py`). Routes in `web/routes/` are strictly limited to HTTP parameter parsing, service delegation, and response formatting.
2. **In-Memory Model Residency:** Models are loaded into process memory once during startup (`model_loader.py`), completely avoiding disk I/O on inference requests.
3. **Zero Database Persistence:** Uploaded files and generated ELA images live only in temporary session directories (`temp/uploads/<session_id>/`) and are purged following report generation or after 30 minutes of inactivity.

### Positive Consequences:
- High performance ($< 5\text{ s}$ total analysis turnaround).
- Strict user privacy with zero data footprint.
- Clean separation making unit testing and mocking trivial.

## Status
**ACCEPTED** (2026-11-08)
