## 2026-05-15 - Startup Observability Hardening

### Added
- Added structured JSON stdout logging for backend runtime logs.
- Added regression coverage for startup mock-device seed failures so they are logged instead of silently swallowed.

### Changed
- `backend/main.py` now logs mock-device seed startup failures with exception context while still allowing FastAPI startup to continue when Home Assistant is unavailable.

## 2026-05-15 08:30 ADT - Security + Container Hygiene Follow-up

### Changed
- Documented API-key enforcement for control endpoints (`/devices`, `/services`, `/commands`, `/mock/*`) using `SMART_HOME_API_KEY` and `X-API-Key`.
- Documented diagnostic endpoints that remain unauthenticated (`GET /`, `GET /ha/health`).
- Documented root `.dockerignore` requirement for Docker builds to exclude `.env*`, `config/`, `homeassistant/`, virtualenvs, logs, and caches from build context.
- Updated `docs/PROJECT_DOC.md` environment example to include `SMART_HOME_API_KEY`.

### Notes
- These doc updates track implementation PRs #4 and #5.

## 2026-05-15 03:25 ADT - HTML API Docs Artifact

### Added
- Added `docs/SMART_HOME_API_DOCS.html`, a standalone dark industrial developer-docs page for the Smart Home HA Backend with sticky navigation, endpoint reference, syntax-highlighted code blocks, tabbed examples, and copy-to-clipboard controls.

### Changed
- Updated `docs/PROJECT_DOC.md` to reference the new HTML docs artifact.
- Refreshed `docs/PROJECT_TREE.md`.

### Notes
- The HTML docs use placeholder/redacted token examples only; no real credentials were copied.

## 2026-05-15 03:16 ADT - Execution Layer Docs

### Changed
- Clarified Hermes-side execution versus FastAPI endpoint handling and backend command/action execution in `docs/BACKEND_CODE_GUIDE.md`, `docs/HA_BACKEND_API.md`, `docs/PROJECT_DOC.md`, and `backend/README.md`.
- Documented that `execute_command()` is backend command execution after Hermes sends `POST /commands`, not the Hermes brain itself.

### Notes
- No token values or `.env` contents were copied into documentation.

## 2026-05-15 01:58 ADT - Backend Action Path + HA Env Docs

### Added
- Added `backend/services/action_service.py` as the shared HA action executor for `/commands`, `/services/{domain}/{service}`, and mock power convenience endpoints.
- Added tests for HA env precedence, mock endpoint safety, toggle expected-state verification, and unverifiable-action reporting.

### Changed
- Restored `HA_URL`, `HA_TOKEN`, and `HA_TIMEOUT_SEC` as the preferred backend env keys; `HASS_*` remains only as a commented/backwards-compatible fallback.
- Documented `POST /commands` as the canonical production automation endpoint; `/services`, `/devices`, and `/mock` are secondary direct/debug/convenience paths.
- Updated backend/API/code-guide docs to describe the shared action executor and verification semantics.
- Refreshed `docs/PROJECT_TREE.md`.

### Notes
- No token values or `.env` contents were copied into documentation.

## 2026-05-14 14:48 ADT - Doc Sync

### Changed
- Updated `AGENT.md` to enforce canonical docs root `D:\smart_home\docs` and explicitly forbid creating docs under typo path `D:\smarthome`.
- Refreshed `docs/PROJECT_TREE.md` after cleanup.

### Removed
- Removed duplicate typo-root workspace `D:\smarthome` (`/mnt/d/smarthome`) after comparing it against canonical `D:\smart_home`.

### Notes
- Comparison summary before deletion: `/mnt/d/smart_home` had full project tree (~12992 files) while `/mnt/d/smarthome` only contained a small duplicate docs-only subtree (8 files).

     1|# Changelog
     2|
     3|## 2026-05-14 12:47 - Backend Code Guide
     4|
     5|### Added
     6|- Added `BACKEND_CODE_GUIDE.md` with detailed explanations of backend files, classes, functions, request flows, extension rules, and maintenance notes.
     7|
     8|### Changed
     9|- Updated wiki index/project entity to link to the new backend code guide as the source of truth for code explanations.
    10|- Refreshed `PROJECT_TREE.md`.
    11|
    12|### Notes
    13|- Chose a detailed docs page instead of heavy inline code comments so the code stays clean while future readers get a full walkthrough.
    14|
    15|## 2026-05-14 12:41 - Docs Dedup Cleanup
    16|
    17|### Removed
    18|- Removed stale duplicate docs: `PROJECT_DOC.md`, `backend_log.md`, `alias.md`, `get_state_json`, and `HA_API_PathTree.md`.
    19|- Removed stale wiki raw snapshots and duplicate wiki entity/query pages that repeated old doc-sync state.
    20|
    21|### Changed
    22|- Kept backend API details centralized in `HA_BACKEND_API.md`.
    23|- Kept project history centralized in `CHANGELOG.md`.
    24|- Rewrote wiki pages as a concise index/knowledge layer instead of a duplicate API or changelog copy.
    25|- Refreshed `PROJECT_TREE.md`.
    26|
    27|### Notes
    28|- No secrets or Home Assistant auth/state dump contents were copied into docs.
    29|
    30|## 2026-05-14 14:02 - Modular Backend Refactor
    31|
    32|### Changed
    33|- Split `backend/main.py` into maintainable layers: `routers/`, `services/`, `schemas/`, and `core/`.
    34|- Kept `main.py` thin: app construction, router registration, and startup mock-device seeding only.
    35|- Added room-based default mock device catalog in `services/default_devices.py`.
    36|
    37|### Added
    38|- Added seeded mock devices for bedroom, living room, kitchen, and bathroom.
    39|- Added `GET /mock/rooms` to expose default mock devices grouped by room.
    40|- Expanded tests to verify modular router structure and default room/device catalog.
    41|
    42|### Verified
    43|- Ran backend unit tests successfully: `.venv/Scripts/python.exe -m unittest tests/test_backend_api.py -v`.
    44|- Ran Python compile check across `main.py`, `ha_client.py`, `core/`, `schemas/`, `services/`, `routers/`, and tests.
    45|- Seeded 4 mock devices into the running Home Assistant container.
    46|- Verified live `/commands` flow for `switch.mock_kitchen_plug` returns `success`, state `on`, verified `true`.
    47|
    48|## 2026-05-14 13:45 - HA Backend API Implementation
    49|
    50|### Added
    51|- Implemented complete Home Assistant FastAPI bridge in `D:\smart_home\backend`.
    52|- Added HA health/config, state, service-call, Hermes-style command, and mock-device APIs.
    53|- Added built-in mock test device: `light.mock_bedroom_lamp`.
    54|- Added backend unit tests: `tests/test_backend_api.py`.
    55|- Added `HA_BACKEND_API.md` with API examples and instructions for changing/adding real devices later.
    56|
    57|### Verified
    58|- Home Assistant container API responded with `API running.`.
    59|- Created/updated `light.mock_bedroom_lamp` in the running HA container.
    60|- Verified `/commands` can turn the mock bedroom lamp off and confirm HA state changed to `off`.
    61|- Ran backend tests successfully with `.venv/Scripts/python.exe -m unittest tests/test_backend_api.py -v`.
    62|
    63|## 2026-05-13 14:32 - Doc Sync
    64|
    65|### Changed
    66|- No meaningful workspace changes detected from git status.
    67|- Updated `docs/PROJECT_TREE.md`
    68|
    69|### Notes
    70|- git status unavailable; using filesystem snapshot only
    71|- Excluded noisy/generated paths and sensitive env/auth/token/secret files from documentation outputs.
    72|
    73|## 2026-05-11 14:02 - Doc Sync
    74|
    75|### Notes
    76|- Workspace tree changed (files/directories added, removed, or renamed).
    77|- No local AGENT instructions found.
    78|- Wiki/doc sync run completed and logged.
    79|
    80|### Changed
    81|- Refreshed `docs/PROJECT_TREE.md`.
    82|- Updated wiki run source and linked wiki pages under `/mnt/d/smart_home/docs/wiki`.
    83|
    84|## 2026-05-10 14:01 - Doc Sync
    85|
    86|### Notes
    87|- No meaningful workspace file changes detected from git status.
    88|
    89|### Changed
    90|- Refreshed `docs/PROJECT_TREE.md`.
    91|- Refreshed wiki index and run tracking under `/mnt/d/smart_home/docs/wiki`.
    92|
    93|### Notes
    94|- No local AGENT instructions found.
    95|