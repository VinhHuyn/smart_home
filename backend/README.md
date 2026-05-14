# 🧠 Backend Run Guide (FastAPI + Home Assistant)

This backend is the Smart Home API bridge for Home Assistant. It exposes Home Assistant health/config, device states, service calls, Hermes-style command messages, and expandable mock devices for local testing.

## Architecture layout

The backend is intentionally split by layer. Do **not** dump future logic into `main.py`.

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
 │   ├── command_service.py          # Hermes command execution logic
 │   ├── default_devices.py          # seed mock rooms/devices
 │   ├── ha_service.py               # HA service-call orchestration
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

- `routers/` should only parse HTTP requests and return HTTP responses.
- `services/` owns business logic and Home Assistant orchestration.
- `schemas/` owns Pydantic models.
- `core/` owns shared helpers.
- `ha_client.py` owns raw HA REST calls only.
- `main.py` should stay small: app setup + router includes + startup seed.

## Configure environment

Create/edit `.env`:

```env
HA_URL=http://localhost:8123
HA_TOKEN=YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN
HA_TIMEOUT_SEC=10
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

## Main endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | backend status/capabilities |
| `GET` | `/ha/health` | Home Assistant API check |
| `GET` | `/ha/config` | Home Assistant config metadata |
| `GET` | `/devices` | list HA states |
| `GET` | `/devices/{entity_id}` | read one HA state |
| `POST` | `/devices/{entity_id}/state` | set one HA state |
| `DELETE` | `/devices/{entity_id}` | delete one HA state |
| `GET` | `/services` | list HA services |
| `GET` | `/services/{domain}` | list one service domain |
| `POST` | `/services/{domain}/{service}` | call HA service |
| `POST` | `/commands` | Hermes Brain → HA Operator command schema |
| `GET` | `/mock/rooms` | list default mock devices grouped by room |
| `GET` | `/mock/devices` | list mock devices currently in HA |
| `POST` | `/mock/devices` | add mock device |
| `POST` | `/mock/devices/{entity_id}/turn_on` | turn on mock |
| `POST` | `/mock/devices/{entity_id}/turn_off` | turn off mock |
| `POST` | `/mock/devices/{entity_id}/toggle` | toggle mock |

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
services/default_devices.py
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

Then restart backend. The startup hook in `main.py` will seed it into HA.

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
