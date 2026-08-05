# RAG Video Insight — Streamlit frontend

A production-minded Streamlit client for a NestJS RAG video API. It supports registration, authenticated account management, video analysis, a searchable video library, persisted chat sessions, and streamed grounded chat over Server-Sent Events.

## Setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Set `API_BASE_URL` to the address used by your NestJS backend. The supplied `.env.example` uses `http://localhost:3000/api/v1`:

```env
API_BASE_URL=http://localhost:3000/api/v1
```

## API integration

All endpoint calls and response-envelope handling live in `api_client.py`. The client accepts common NestJS conventions (`data` envelopes, camel/snake case job IDs and tokens) without coupling the presentation layer to one exact backend DTO.

Authenticated requests automatically attach `Authorization: Bearer <access-token>`. The app attempts to refresh a session before returning the user to sign-in. SSE chat consumes `token`, `done`, and `error` events and renders tokens live.

The API client centralizes payload-envelope and collection mapping. If your NestJS DTO uses different field names, update only the helpers in `api_client.py` rather than individual views.

## Features

- YouTube and Instagram URL validation with processing-state polling and retry controls.
- Authenticated video library with search, metadata, and saved conversation entry points.
- Multiple named chat sessions per video, persisted message history, and conversation deletion.
- Transcript/context preview plus source/timestamp placeholders for grounded answers.
- Deep slate interface with responsive cards, empty states, loading states, and error feedback.

## Project layout

```
app.py              # Entry point and auth screen
api_client.py       # REST + SSE client and centralized response mapping
auth.py              # Streamlit session auth helpers
pages/               # Dashboard and chat workspace
components/          # Shared visual components
```
