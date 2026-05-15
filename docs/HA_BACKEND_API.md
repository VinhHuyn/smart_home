# Home Assistant Backend API

_Last updated: 2026-05-15T19:54:00Z_

This document describes the modular FastAPI backend in `D:\smart_home\backend` that bridges Hermes / chat commands to the running Home Assistant container.

## Runtime roles

- **Home Assistant container**: runs at `http://localhost:8123` and owns the real HA state machine.
- **Backend API**: runs from `D:\smart_home\backend` and exposes structured APIs for states, service calls, command messages, and mock devices.
- **Mock devices**: virtual HA states created through `/api/states`. They do not require physical hardware.

## Backend architecture

The backend is now split into maintainable layers:

```text
backend/
├── main.py
├── ha_client.py
├── core/
│   ├── errors.py
│   └── time.py
├── schemas/
│   └── ha.py
├── services/
│   ├── action_service.py
│   ├── command_service.py
│   ├── default_devices.py
│   ├── ha_service.py
│   └── mock_device_service.py
├── routers/
│   ├── commands.py
│   ├── devices.py
│   ├── health.py
│   ├── mock_devices.py
│   └── services.py
└── tests/
    └── test_backend_api.py
```

Maintenance rules:

- Keep `main.py` thin: app creation, router registration, startup hooks only.
- Add new HTTP endpoints in `routers/`.
- Add business logic in `services/`.
- Keep duplicated HA action behavior in `services/action_service.py` so `/commands`, `/services`, and mock power endpoints share payload construction, mock state updates, and verification.
- Add request/response models in `schemas/`.
- Add shared utilities in `core/`.
- Keep raw Home Assistant REST calls in `ha_client.py`.

## Environment

Create or update `D:\smart_home\backend\.env`:

```env
HA_URL=http://localhost:8123
HA_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
HA_TIMEOUT_SEC=10

# Optional fallback for older Orin cutover configs only:
# HASS_URL=http://localhost:8123
# HASS_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
# HASS_TIMEOUT_SEC=10
```

The backend prefers `HA_*`. If both `HA_*` and `HASS_*` are present, `HA_*` wins. Keep `HASS_*` commented out unless you intentionally need the fallback path.

Do not commit `.env` or Home Assistant auth/storage files.

## Authentication

Control/data endpoints require the shared backend API key:

```http
X-API-Key: <SMART_HOME_API_KEY>
```

Protected endpoint groups: `/devices`, `/services`, `/commands`, and `/mock/*`. Public diagnostic endpoints: `GET /` and `GET /ha/health`.

## Run backend

PowerShell:

```powershell
cd D:\smart_home\backend
.\.venv\Scripts\activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

WSL:

```bash
cd /mnt/d/smart_home/backend
.venv/Scripts/python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

## Who executes what?

Use this ownership model to avoid confusing Hermes execution with backend/API execution:

```text
User text / Discord
  -> Hermes Brain or Orin Hermes agent
     - understands natural language
     - selects domain/service/entity_id
     - sends HTTP POST /commands

POST /commands
  -> routers/commands.py
     - API endpoint layer
     - receives and validates CommandRequest

services/command_service.py
  -> execute_command(request)
     - backend command execution wrapper
     - converts command intent into ActionRequest

services/action_service.py
  -> execute_ha_action(...)
     - canonical HA action executor
     - chooses mock state update vs real HA service call
     - performs verification

ha_client.py
  -> raw Home Assistant REST calls
```

So `execute_command()` is not the Hermes brain. It is the backend function called after Hermes has already converted natural language into a structured `POST /commands` payload.

## API overview

### Service metadata

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Backend health and capability list |
| `GET` | `/ha/health` | Check Home Assistant REST API connectivity |
| `GET` | `/ha/config` | Read Home Assistant config metadata |

### Device states

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/devices` | List all HA entity states |
| `GET` | `/devices/{entity_id}` | Read one HA entity state |
| `PUT` | `/devices/{entity_id}?state=off` | Backward-compatible state update |
| `POST` | `/devices/{entity_id}/state` | Set state with JSON body |
| `DELETE` | `/devices/{entity_id}` | Delete a HA state entity |

### Home Assistant services

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/services` | List all HA service domains/actions |
| `GET` | `/services/{domain}` | List services for one HA domain |
| `POST` | `/services/{domain}/{service}` | Secondary direct service-call path; shares `services/action_service.py` behavior with `/commands` |

Example real service call:

```bash
curl -X POST http://127.0.0.1:8000/services/light/turn_off \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SMART_HOME_API_KEY" \
  -d '{"entity_id":"light.real_bedroom_lamp","require_verification":true}'
```

For real devices, this endpoint calls HA `/api/services/{domain}/{service}`.

### Hermes-style command endpoint

`POST /commands` accepts the Brain-Hermes → Orin/HA-operator schema. This is the canonical production automation endpoint; `/services`, `/devices`, and `/mock` are secondary direct/debug/convenience paths.

Example for bedroom light off:

```bash
curl -X POST http://127.0.0.1:8000/commands \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SMART_HOME_API_KEY" \
  -d '{
    "schema_version":"ha-bridge.v1",
    "message_type":"ha.command.request",
    "request_id":"req_manual_bedroom_off_001",
    "source":{"agent":"hermes-brain","host":"pc-main"},
    "target":{"agent":"hermes-orin","host":"orin-edge"},
    "user_context":{"platform":"discord","original_text":"turn off bedroom light"},
    "intent":{"domain":"light","service":"turn_off","entity_id":"light.mock_bedroom_lamp","area_id":"bedroom","confidence":0.98},
    "execution_policy":{"dry_run":false,"require_verification":true,"verify_timeout_sec":10,"max_retries":0},
    "safety":{"priority":"normal","allow_destructive":false,"requires_user_confirmation":false}
  }'
```

Successful result shape:

```json
{
  "schema_version": "ha-bridge.v1",
  "message_type": "ha.command.result",
  "request_id": "req_manual_bedroom_off_001",
  "status": "success",
  "ha_call": {
    "domain": "light",
    "service": "turn_off",
    "entity_id": "light.mock_bedroom_lamp"
  },
  "verification": {
    "performed": true,
    "state_before": "on",
    "state_after": "off",
    "expected_state": "off",
    "verified": true
  }
}
```

## Mock room/device support

The backend seeds multiple mock devices when possible. Catalog source:

```text
D:\smart_home\backend\services\default_devices.py
```

Seeded devices:

| Room | Entity ID | Domain | Type |
|---|---|---|---|
| bedroom | `light.mock_bedroom_lamp` | `light` | lamp |
| living_room | `light.mock_living_room_lamp` | `light` | lamp |
| kitchen | `switch.mock_kitchen_plug` | `switch` | plug |
| bathroom | `light.mock_bathroom_light` | `light` | ceiling light |

Mock device endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/mock/rooms` | List default mock devices grouped by room |
| `GET` | `/mock/devices` | List HA entities marked as mock devices |
| `POST` | `/mock/devices` | Create/register a mock HA state entity |
| `POST` | `/mock/devices/{entity_id}/turn_on` | Set a mock device to `on` |
| `POST` | `/mock/devices/{entity_id}/turn_off` | Set a mock device to `off` |
| `POST` | `/mock/devices/{entity_id}/toggle` | Toggle mock device state |

Create a new mock device at runtime:

```bash
curl -X POST http://127.0.0.1:8000/mock/devices \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id":"light.test_lamp",
    "name":"Test Lamp",
    "domain":"light",
    "room":"test_room",
    "initial_state":"off",
    "attributes":{"device_type":"lamp"}
  }'
```

Turn on/off mock device:

```bash
curl -X POST http://127.0.0.1:8000/mock/devices/light.mock_bedroom_lamp/turn_on
curl -X POST http://127.0.0.1:8000/mock/devices/light.mock_bedroom_lamp/turn_off
```

Important: mock `light` and `switch` commands sent to `/commands` are handled through HA state updates, not physical HA service calls. This makes them reliable for testing without hardware.

## How to add or change mock devices later

For persistent mock devices, edit:

```text
D:\smart_home\backend\services\default_devices.py
```

Add another `MockDeviceCreate` entry:

```python
MockDeviceCreate(
    entity_id="light.mock_office_lamp",
    name="Mock Office Lamp",
    domain="light",
    room="office",
    initial_state="off",
    attributes={"room": "office", "device_type": "lamp"},
)
```

Then restart backend. Startup seeding will create/update it in HA.

## How to add or change actual devices later

When real devices are added to Home Assistant:

1. Pair/configure the real device inside Home Assistant.
2. Find its actual `entity_id` in Home Assistant Developer Tools → States.
3. Replace mock entity IDs in caller prompts/config with the real entity ID.
4. Use the same `/commands` schema:
   - `intent.domain`: HA domain, e.g. `light`, `switch`, `climate`, `cover`, `lock`.
   - `intent.service`: HA service, e.g. `turn_on`, `turn_off`, `set_temperature`.
   - `intent.entity_id`: real HA entity ID, e.g. `light.bedroom_ceiling`.
   - `intent.service_data`: extra HA service fields when needed.
5. For verification, set `execution_policy.require_verification=true` and optionally `execution_policy.expected_state`.

## Test command

Run backend tests from WSL:

```bash
cd /mnt/d/smart_home/backend
.venv/Scripts/python.exe -m unittest tests/test_backend_api.py -v
```

Expected result: all tests pass.

## Runtime logging

PR #11 adds structured JSON logs to stdout so Docker/container log collectors can parse backend runtime events. Startup mock-device seed failures are logged with exception context while startup continues if Home Assistant is unavailable.

Check container logs:

```bash
docker logs smart-home-backend --tail 50
```

Expected error shape after a startup seed failure:

```json
{"level":"ERROR","logger":"main","message":"Failed to seed default mock devices","exception":"..."}
```
