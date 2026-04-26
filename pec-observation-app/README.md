# PEC Observation App

Native Apple iOS/iPadOS application for PECs (Professores Especialistas de Currículo) — pedagogical observation, recording, transcription, AI feedback, and action plans.

## Architecture

```
iOS App (Swift/SwiftUI)          Backend (Python FastAPI)
  Offline-first                    10 Microservices
  SwiftData                        PostgreSQL (per service)
  AVFoundation                     Redis Streams (events)
  Hexagonal                        MinIO (object storage)
  MVVM + Use Cases                 Hexagonal architecture
```

## MVP Phasing

| MVP | Features | Services |
|-----|----------|----------|
| 1 | School/Teacher CRUD, Observation, Recording offline, Audio sync | MS-001 to MS-004, MS-009 |
| 2 | Transcription, AI Feedback, Human Review, Action Items | MS-005 to MS-007, MS-010 |
| 3 | PDF Export, Audit, RBAC, Retention | MS-008, full compliance |

## Running the Backend

```bash
cp .env.example .env
docker compose up
```

Services start on:
- MS-001 Identity: http://localhost:8001
- MS-002 School: http://localhost:8002
- MS-003 Observation: http://localhost:8003
- MS-004 Audio Ingestion: http://localhost:8004
- MS-005 Transcription: http://localhost:8005
- MS-006 AI Feedback: http://localhost:8006
- MS-007 Feedback: http://localhost:8007
- MS-008 PDF Export: http://localhost:8008
- MS-009 Audit: http://localhost:8009
- MS-010 Consent: http://localhost:8010

MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

## Running with Ollama (LLM)

```bash
docker compose --profile llm up
docker exec -it $(docker compose ps -q ollama) ollama pull llama3.2
```

## Tests

```bash
# Backend smoke tests (requires docker compose up)
cd tests && pip install httpx pytest
pytest smoke/ -v

# Integration tests
pytest integration/ -v

# Service unit tests (standalone)
cd services/ms-003-observation
pip install -e ../../shared -r requirements.txt pytest
pytest tests/ -v

# iOS domain unit tests (Linux-compatible, no iOS runtime needed)
# Requires Swift toolchain
cd ios-app && swift test
```

## iOS App

Open `ios-app/` in Xcode on a Mac (iOS 17+). Set `PEC_API_BASE_URL` in Info.plist to point to your backend.

The app architecture follows hexagonal design:
- `Domain/` — pure Swift entities, no frameworks
- `Ports/` — protocol abstractions
- `Application/UseCases/` — business logic (testable on Linux)
- `Adapters/` — SwiftData, AVFoundation, URLSession, SwiftUI

## Event Flow

```
iOS → MS-004 presigned URL → PUT audio → MS-004 confirm
                                          ↓ audio.uploaded event
                                    MS-005 Whisper transcription
                                          ↓ transcription.completed
                                    MS-006 Ollama AI feedback
                                          ↓ ai_feedback.generated
                                    MS-007 Feedback draft created
                                    MS-008 PDF on approval
                                    MS-009 Audit all events
                                    MS-010 Schedule audio deletion
```

## Non-Functional Requirements

- **Offline-first**: All field operations work without internet
- **Security**: Tokens in Keychain, audio with iOS data protection
- **Compliance**: LGPD audio retention (7 days default), audit trail
- **Cloud agnostic**: All providers behind adapter interfaces
