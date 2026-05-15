# 🏠 Smart Home Project Guide (FastAPI + Home Assistant)

This repository hosts the Smart Home backend bridge for Home Assistant. The backend exposes Home Assistant health/config, device states, service calls, Hermes-style command messages, and expandable mock devices for local testing.

## Repo layout

```text
D:\smart_home
 ├── backend/      # FastAPI Home Assistant bridge
 ├── docs/         # Project documentation and generated API docs
 └── .github/      # CI workflows and repository automation
```

## Architecture layout (backend)

Backend code lives in `backend/` and is intentionally split by layer. Do **not** dump future logic into `backend/main.py`.

```text
D:\smart_home\backend
 ├── main.py                         # app creation, router registration, startup hooks only
 ├── ha_client.py                    # low-level Home Assistant REST client
 ├── core\
 │   ├── errors.py                   # shared FastAPI error mapping
 │   └── time.py                     # shared UTC timestamp helper
 ├── schemas\
 │   └── ha.py                       # Pydantic request/response models
 ├── services\
 │   ├── action_service.py           # shared HA action execution + verification
 │   ├── command_service.py          # Hermes command execution wrapper
 │   ├── default_devices.py          # seed mock rooms/devices
 │   ├── ha_service.py               # secondary HA service-call wrapper
 │   └── mock_device_service.py      # mock device state logic
 ├── routers\
 │   ├── commands.py                 # /commands API
 │   ├── devices.py                  # /devices API
 │   ├── health.py                   # / and /ha/* API
 │   ├── mock_devices.py             # /mock/* API
 │   └── services.py                 # /services API
 ├── tests\test_backend_api.py
 ├── requirements.txt
 └── .env
```

Layer rule:

- `backend/routers/` should only parse HTTP requests and return HTTP responses.
- `backend/services/` owns business logic and Home Assistant orchestration.
- `backend/schemas/` owns Pydantic models.
- `backend/core/` owns shared helpers.
- `backend/ha_client.py` owns raw HA REST calls only.
- `backend/main.py` should stay small: app setup + router includes + startup seed.

## Configure environment

> If you containerize this backend from the repository root, keep `.dockerignore` present so secrets (`.env`, `config/`) and local virtualenv files are not sent into Docker build context. If you build with `context: ./backend`, keep `backend/.dockerignore` present too; Docker only reads the ignore file inside the selected build context.


Create/edit `backend/.env`:

```env
HA_URL=http://localhost:8123
HA_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
HA_TIMEOUT_SEC=10
SMART_HOME_API_KEY=CHANGE_ME_STRONG_RANDOM_KEY

# Backwards-compatible fallback only; keep commented out unless needed:
# HASS_URL=http://localhost:8123
# HASS_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
# HASS_TIMEOUT_SEC=10
```

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

Open API docs:

```text
http://127.0.0.1:8000/docs
```

## API authentication

All control/data endpoints (`/devices`, `/services`, `/commands`, `/mock/*`) require:

```http
X-API-Key: <SMART_HOME_API_KEY>
```

Public endpoints kept unauthenticated for diagnostics:
- `GET /`
- `GET /ha/health`

## Canonical control path

Use **`POST /commands`** for production automation and Hermes Brain → HA Operator control. It is the canonical path because it includes a stable command schema, before/after state reads, mock-device handling, and verification metadata.

The other endpoints are kept as compatibility/debug paths:

- `/services/{domain}/{service}`: direct HA-style service calls for manual testing and low-level tooling.
- `/mock/devices/*`: mock-device convenience endpoints.
- `/devices/*`: raw HA state inspection/update helpers.

To avoid duplicated behavior, `/commands`, `/services/{domain}/{service}`, and mock power endpoints now share the same service helper in `backend/services/action_service.py` for turn on/off/toggle, mock state updates, service payload construction, and verification.

## Execution ownership

Do not confuse Hermes execution with backend execution:

| Layer | File/place | Job |
|---|---|---|
| Hermes agent/tool/client | outside this FastAPI backend | Convert user text like `bed light on` into a structured command and call `POST /commands` |
| API endpoint | `routers/commands.py` | Receive and validate the HTTP request |
| Command service | `services/command_service.py` | `execute_command()` converts the Hermes command envelope into an action request |
| Action service | `services/action_service.py` | `execute_ha_action()` controls mock/real HA entities and verifies state |
| HA client | `ha_client.py` | Performs raw Home Assistant REST calls |

`execute_command()` is backend command execution. It is not the Hermes brain; Hermes has already acted by the time this function runs.

## Main endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | backend status/capabilities |
| `GET` | `/ha/health` | Home Assistant API check |
| `GET` | `/ha/config` | Home Assistant config metadata |
| `GET` | `/devices` | list HA states |
| `GET` | `/devices/{entity_id}` | read one HA state |
| `POST` | `/devices/{entity_id}/state` | set one HA state/debug helper |
| `DELETE` | `/devices/{entity_id}` | delete one HA state/debug helper |
| `GET` | `/services` | list HA services |
| `GET` | `/services/{domain}` | list one service domain |
| `POST` | `/services/{domain}/{service}` | secondary direct service-call path |
| `POST` | `/commands` | canonical Hermes Brain → HA Operator command schema |
| `GET` | `/mock/rooms` | list default mock devices grouped by room |
| `GET` | `/mock/devices` | list mock devices currently in HA |
| `POST` | `/mock/devices` | add mock device |
| `POST` | `/mock/devices/{entity_id}/turn_on` | secondary mock convenience path |
| `POST` | `/mock/devices/{entity_id}/turn_off` | secondary mock convenience path |
| `POST` | `/mock/devices/{entity_id}/toggle` | secondary mock convenience path |

## Seeded mock rooms/devices

Startup seeds these virtual devices into HA when HA is reachable:

| Room | Entity ID | Type |
|---|---|---|
| bedroom | `light.mock_bedroom_lamp` | lamp |
| living_room | `light.mock_living_room_lamp` | lamp |
| kitchen | `switch.mock_kitchen_plug` | plug/switch |
| bathroom | `light.mock_bathroom_light` | ceiling light |

Check default room catalog:

```bash
curl http://127.0.0.1:8000/mock/rooms
```

Turn a mock device on/off through backend:

```bash
curl -X POST http://127.0.0.1:8000/mock/devices/light.mock_bedroom_lamp/turn_on
curl -X POST http://127.0.0.1:8000/mock/devices/light.mock_bedroom_lamp/turn_off
```

Hermes-style command:

```bash
curl -X POST http://127.0.0.1:8000/commands \
  -H "Content-Type: application/json" \
  -d '{
    "schema_version":"ha-bridge.v1",
    "message_type":"ha.command.request",
    "request_id":"req_manual_bedroom_off_001",
    "intent":{"domain":"light","service":"turn_off","entity_id":"light.mock_bedroom_lamp"},
    "execution_policy":{"require_verification":true}
  }'
```

## Add/change mock devices later

Edit:

```text
backend/services/default_devices.py
```

Add one `MockDeviceCreate(...)` entry:

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

Then restart backend. The startup hook in `backend/main.py` will seed it into HA.

## Add/change real devices later

1. Add/pair the physical device in Home Assistant.
2. Find its `entity_id` in HA Developer Tools → States.
3. Use the same `/commands` payload, replacing only:
   - `intent.domain`
   - `intent.service`
   - `intent.entity_id`
   - optional `intent.service_data`
4. For non-light/switch devices, set `execution_policy.expected_state` when verification cannot infer the state automatically.

Example real light:

```json
{
  "intent": {
    "domain": "light",
    "service": "turn_off",
    "entity_id": "light.bedroom_ceiling"
  },
  "execution_policy": {
    "require_verification": true
  }
}
```

Example climate call:

```json
{
  "intent": {
    "domain": "climate",
    "service": "set_temperature",
    "entity_id": "climate.bedroom_ac",
    "service_data": {
      "temperature": 23,
      "hvac_mode": "cool"
    }
  },
  "execution_policy": {
    "require_verification": false
  }
}
```

## Run tests

```bash
cd /mnt/d/smart_home/backend
.venv/Scripts/python.exe -m unittest tests/test_backend_api.py -v
```
