# Smart Home Project Overview

_Last updated: 2026-05-15 03:25 ADT_

## Purpose

`D:\smart_home` is a Home Assistant smart-home backend project. It provides a FastAPI bridge for Home Assistant health/config, device states, service calls, mock devices, and Hermes-style command messages.

## Main components

- `backend/main.py` — thin FastAPI bootstrap and router registration.
- `backend/ha_client.py` — raw Home Assistant REST client. It prefers `HA_URL`, `HA_TOKEN`, and `HA_TIMEOUT_SEC`; `HASS_*` is only a fallback for older configs.
- `backend/services/action_service.py` — canonical shared HA action executor for payload construction, mock-device handling, before/after reads, and verification.
- `backend/services/command_service.py` — wraps canonical action execution in the Hermes `ha.command.request` / `ha.command.result` schema.
- `backend/services/ha_service.py` — secondary direct service-call wrapper that reuses the canonical action executor.
- `backend/services/mock_device_service.py` — mock-device creation/listing plus convenience power endpoints; mock power endpoints require `attributes.mock_device: true`.
- `backend/routers/` — HTTP route modules.
- `backend/tests/test_backend_api.py` — backend unit tests.
- `docs/HA_BACKEND_API.md` — endpoint and environment reference.
- `docs/BACKEND_CODE_GUIDE.md` — file-by-file backend explanation.
- `docs/SMART_HOME_API_DOCS.html` — standalone dark-themed HTML developer docs artifact.

## Canonical control path

Use `POST /commands` for production Hermes automation. It is the stable command envelope and includes verification metadata.

Execution ownership is split deliberately:

- **Hermes execution** lives outside this backend: interpret user text, choose `domain`, `service`, and `entity_id`, then send HTTP to `/commands`.
- **API endpoint code** lives in `backend/routers/`: receive and validate HTTP requests.
- **Backend command/action execution** lives in `backend/services/`: `execute_command()` wraps the Hermes command schema, and `execute_ha_action()` performs mock/real HA control plus verification.

`execute_command()` is therefore backend execution, not the Hermes brain itself.

Secondary paths remain available for debugging and compatibility:

- `/services/{domain}/{service}` — direct HA-style service call wrapper.
- `/devices/*` — raw state inspection/update helpers.
- `/mock/*` — mock-device catalog and convenience controls.

## Environment convention

Use `backend/.env` with:

```env
HA_URL=http://localhost:8123
HA_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
HA_TIMEOUT_SEC=10

# Optional fallback only; keep commented unless intentionally used:
# HASS_URL=http://localhost:8123
# HASS_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
# HASS_TIMEOUT_SEC=10
```

Do not commit `.env`, Home Assistant auth storage, tokens, or raw private state dumps.

## Recent notable changes

- Reduced duplicated behavior across `/commands`, `/services`, and mock power endpoints by routing them through `services/action_service.py`.
- Restored `HA_*` as the preferred backend environment key family after Orin HA token cutover.
- Tightened mock endpoint safety so mock convenience routes do not accidentally control real devices.
- Clarified documentation for which execution layer belongs to Hermes, API endpoints, and backend services.
- Added a self-contained HTML API documentation page with sticky navigation, syntax-highlighted code blocks, endpoint reference, and copy buttons.

## Validation

Current backend validation command:

```bash
cd /mnt/d/smart_home/backend
.venv/Scripts/python.exe -m unittest tests/test_backend_api.py -v
.venv/Scripts/python.exe -m py_compile main.py ha_client.py core/*.py schemas/*.py services/*.py routers/*.py tests/test_backend_api.py
```
