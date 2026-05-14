# Backend Code Guide

_Last updated: 2026-05-14 12:47 ADT_

This guide explains what each backend file, class, function, and main flow does. It is meant for future maintenance, so the code can stay clean while this document carries the detailed explanation.

Project paths:

```text
Windows: D:\smart_home\backend
WSL:     /mnt/d/smart_home/backend
```

## High-level architecture

The backend is a FastAPI bridge between Hermes/chat commands and Home Assistant.

```text
User / Hermes
   ↓
FastAPI routers/       HTTP endpoint layer
   ↓
services/              business logic and command orchestration
   ↓
ha_client.py           raw Home Assistant REST API client
   ↓
Home Assistant REST API
```

Layer rules:

- `main.py` should stay thin: create the FastAPI app, register routers, and run startup seeding.
- `routers/` should only parse HTTP requests and return HTTP responses.
- `services/` should contain business decisions and multi-step workflows.
- `schemas/` should define request/response data shapes.
- `core/` should hold small shared helpers.
- `ha_client.py` should be the only layer that directly talks to Home Assistant REST endpoints.

## Request flow examples

### Hermes command flow: `POST /commands`

```text
POST /commands
  -> routers/commands.py: command()
  -> services/command_service.py: execute_command()
  -> ha_client.py: get_state(), set_state(), or call_service()
  -> Home Assistant
  -> response shaped as ha.command.result
```

This is the best endpoint for Hermes automation because it supports:

- request IDs
- source/target metadata
- dry-run mode
- state verification
- explicit expected state
- real-device service calls
- mock-device handling

### Mock device manual test flow

```text
POST /mock/devices/light.mock_bedroom_lamp/turn_on
  -> routers/mock_devices.py: turn_on_mock_device()
  -> services/mock_device_service.py: set_mock_device_power()
  -> ha_client.py: set_state()
  -> Home Assistant /api/states/{entity_id}
```

This is useful for quick testing because it directly changes the virtual HA entity state without requiring physical hardware.

### Real Home Assistant service flow

```text
POST /services/light/turn_off
  -> routers/services.py: call_service()
  -> services/ha_service.py: call_service()
  -> ha_client.py: call_service()
  -> Home Assistant /api/services/light/turn_off
```

Use this when you want to call a Home Assistant domain/service directly.

---

# File-by-file reference

## `main.py`

Purpose: FastAPI application entrypoint.

Important objects/functions:

### `app = FastAPI(...)`

Creates the backend web application with title, description, and version metadata. FastAPI uses this object to serve routes and generate Swagger docs at `/docs`.

### `app.include_router(...)`

Registers each router module:

- `health.router` -> `/`, `/ha/health`, `/ha/config`
- `devices.router` -> `/devices/*`
- `services.router` -> `/services/*`
- `commands.router` -> `/commands`
- `mock_devices.router` -> `/mock/*`

### `seed_mock_devices_on_startup()`

Runs when the FastAPI server starts.

What it does:

1. Calls `seed_default_mock_devices()`.
2. Creates/updates the default mock entities in Home Assistant.
3. Catches all exceptions so the backend can still start even if Home Assistant is offline.

Why it catches exceptions: startup should not crash just because HA is not available. Connectivity can be checked separately with `GET /ha/health`.

---

## `ha_client.py`

Purpose: Low-level Home Assistant REST API client.

This file owns HTTP calls to Home Assistant. Other files should use its functions/classes instead of calling `requests` directly.

### `HomeAssistantError`

Custom exception raised when:

- Home Assistant cannot be reached.
- Home Assistant returns HTTP status `>= 400`.
- The request fails at the network layer.

Fields:

- `message`: human-readable error.
- `status_code`: HA HTTP status code, if available.
- `payload`: HA response body, if available.

### `HomeAssistantSettings`

Dataclass holding connection settings.

Fields:

- `url`: Home Assistant base URL, default `http://localhost:8123`.
- `token`: Home Assistant long-lived access token from environment.
- `timeout_sec`: request timeout, default `10`.

### `HomeAssistantSettings.from_env()`

Reads environment variables:

- `HA_URL`
- `HA_TOKEN`
- `HA_TIMEOUT_SEC`

It strips trailing `/` from `HA_URL` so path joining is predictable.

### `HomeAssistantClient.__init__(settings=None)`

Creates a client. If no settings are passed, it loads settings from environment.

### `HomeAssistantClient.headers`

Builds request headers.

Always includes:

```text
Content-Type: application/json
```

Includes Authorization only when `HA_TOKEN` exists:

```text
Authorization: Bearer [REDACTED]
```

### `HomeAssistantClient._url(path)`

Converts a relative API path into a full URL.

Example:

```text
/api/states/light.mock_bedroom_lamp
-> http://localhost:8123/api/states/light.mock_bedroom_lamp
```

### `HomeAssistantClient._request(method, path, **kwargs)`

Central HTTP request helper.

What it does:

1. Calls `requests.request()` with method, URL, headers, timeout, and extra kwargs.
2. Parses JSON response when possible.
3. Falls back to text response when response is not JSON.
4. Raises `HomeAssistantError` for network errors or HA HTTP errors.
5. Returns parsed payload for successful responses.

This is the main error boundary between backend logic and Home Assistant.

### `HomeAssistantClient.health()`

Calls:

```text
GET /api/
```

Returns HA API health message. If HA returns a plain string, it wraps it as:

```json
{"message": "..."}
```

### `HomeAssistantClient.get_config()`

Calls:

```text
GET /api/config
```

Returns Home Assistant configuration metadata.

### `HomeAssistantClient.get_states()`

Calls:

```text
GET /api/states
```

Returns all entity states.

### `HomeAssistantClient.get_state(entity_id)`

Calls:

```text
GET /api/states/{entity_id}
```

Returns one entity's state object.

### `HomeAssistantClient.set_state(entity_id, state, attributes=None)`

Calls:

```text
POST /api/states/{entity_id}
```

Creates or updates an HA state entity.

Used heavily for mock devices because mock devices are virtual HA states, not physical hardware.

### `HomeAssistantClient.delete_state(entity_id)`

Calls:

```text
DELETE /api/states/{entity_id}
```

Deletes a state entity. Returns `True` if Home Assistant accepts the delete.

### `HomeAssistantClient.get_services()`

Calls:

```text
GET /api/services
```

Returns all available HA service domains and services.

### `HomeAssistantClient.call_service(domain, service, service_data=None)`

Calls:

```text
POST /api/services/{domain}/{service}
```

Used for real HA actions like:

- `light.turn_on`
- `light.turn_off`
- `switch.toggle`
- `climate.set_temperature`

### `_default_client`

A default shared client instance used by simple function wrappers.

### Backwards-compatible wrapper functions

These functions call `_default_client`:

- `get_states()`
- `get_state(entity_id)`
- `set_state(entity_id, state, attributes=None)`
- `delete_state(entity_id)`
- `get_config()`
- `get_services()`
- `call_service(domain, service, service_data=None)`

They exist so older code can keep calling `ha_client.get_state(...)` directly.

---

## `core/errors.py`

Purpose: Convert backend/HA errors into FastAPI HTTP errors.

### `ha_error_response(exc)`

Takes a `HomeAssistantError` and returns a FastAPI `HTTPException`.

Response status:

- Uses `exc.status_code` when HA gave a status code.
- Defaults to `502 Bad Gateway` when HA was unreachable or status is unknown.

Response detail shape:

```json
{
  "message": "...",
  "ha_status_code": 500,
  "ha_payload": {}
}
```

Why this exists: every router can return consistent HA error responses without duplicating error formatting.

---

## `core/time.py`

Purpose: Shared time helper.

### `utc_now()`

Returns current UTC time in ISO format without microseconds.

Example:

```text
2026-05-14T15:47:00Z
```

Used in command results and verification timestamps.

---

## `schemas/ha.py`

Purpose: Pydantic models for request bodies and command payloads.

These models validate input before service logic runs.

### `DEFAULT_MOCK_DEVICE_ID`

Default example entity ID:

```text
light.mock_bedroom_lamp
```

Used in schema examples.

### `StateUpdate`

Request body for:

```text
POST /devices/{entity_id}/state
```

Fields:

- `state`: target HA state, e.g. `on` or `off`.
- `attributes`: optional HA attributes dictionary.

### `ServiceCallRequest`

Request body for:

```text
POST /services/{domain}/{service}
```

Fields:

- `entity_id`: string, list of strings, or null.
- `service_data`: additional HA service payload.
- `require_verification`: whether to read state before/after and check expected state.
- `expected_state`: override for expected post-call state.

### `MockDeviceCreate`

Request body for creating/registering a mock device.

Fields:

- `entity_id`: HA-style entity ID, e.g. `light.test_lamp`.
- `name`: friendly display name.
- `domain`: HA domain, usually `light` or `switch`.
- `room`: logical room name.
- `initial_state`: starting state, usually `off`.
- `attributes`: extra HA attributes.

### `MockDeviceCreate.validate_entity_id(value)`

Validator that ensures `entity_id` contains a dot.

Valid:

```text
light.mock_lamp
switch.mock_plug
```

Invalid:

```text
mock_lamp
```

Reason: Home Assistant entity IDs require a domain prefix.

### `CommandIntent`

The action Hermes wants Home Assistant to perform.

Fields:

- `domain`: HA domain, e.g. `light`, `switch`, `climate`.
- `service`: HA service, e.g. `turn_on`, `turn_off`, `toggle`.
- `entity_id`: target entity or list of entities.
- `area_id`: optional HA area/room ID.
- `confidence`: optional LLM/NLU confidence from `0` to `1`.
- `service_data`: extra HA service fields.

### `ExecutionPolicy`

Controls how the command is executed.

Fields:

- `dry_run`: if true, return the intended HA call without executing it.
- `require_verification`: if true, verify state when possible.
- `verify_timeout_sec`: intended timeout for future verification logic.
- `max_retries`: intended retry count for future retry logic.
- `idempotency_key`: optional duplicate-request guard for future use.
- `expected_state`: explicit expected state override.

### `CommandRequest`

Full Hermes-style command envelope for `POST /commands`.

Fields:

- `schema_version`: currently `ha-bridge.v1`.
- `message_type`: must be `ha.command.request`.
- `request_id`: generated automatically if caller does not provide one.
- `timestamp`: optional caller timestamp.
- `source`: metadata about caller/agent.
- `target`: metadata about target/agent.
- `user_context`: original platform/user text metadata.
- `intent`: required `CommandIntent`.
- `execution_policy`: command behavior controls.
- `safety`: extra safety metadata.

---

## `services/command_service.py`

Purpose: Main Hermes command execution workflow.

This is the most important service for Hermes -> Home Assistant control.

### `expected_state_for_service(service, explicit_expected_state=None)`

Determines what state should be expected after a service call.

Rules:

- If `explicit_expected_state` is provided, return it.
- If service is `turn_on`, expected state is `on`.
- If service is `turn_off`, expected state is `off`.
- Otherwise return `None`.

Why `toggle` returns `None`: the expected state depends on the previous state unless separately calculated.

### `command_service_data(intent)`

Builds the payload sent to Home Assistant.

What it does:

1. Starts with `intent.service_data`.
2. Adds `entity_id` if present.
3. Adds `area_id` if present and not already inside `service_data`.

Example:

```json
{
  "entity_id": "light.mock_bedroom_lamp",
  "brightness": 120
}
```

### `_is_mock_power_command(before, request, entity_id)`

Checks whether the command should be handled as a mock device state update instead of a real HA service call.

Returns true only when:

- The entity already exists.
- Entity attributes include `mock_device: true`.
- Domain is `light` or `switch`.
- Service is `turn_on`, `turn_off`, or `toggle`.
- `entity_id` is a single string.

Why this matters: Home Assistant service calls do not control virtual states the same way physical devices are controlled. Mock devices are more reliable when updated through `/api/states/{entity_id}`.

### `execute_command(request)`

Runs the full command workflow.

Steps:

1. Compute expected final state.
2. Build Home Assistant service payload.
3. Extract `entity_id` only if it is a single string.
4. If `dry_run` is true, return a planned call without touching HA.
5. If an entity ID exists, read current state before execution.
6. If it is a mock power command, update state directly with `ha_client.set_state()`.
7. Otherwise, call the real HA service with `ha_client.call_service()`.
8. Read state after the command when possible.
9. Verify state if verification is required and expected state is known.
10. Return a structured `ha.command.result` payload.

Important result statuses:

- `dry_run`: command was not executed.
- `success`: command executed and verification passed or was not needed.
- `verification_failed`: command executed but observed state did not match expected state.
- `failed`: Home Assistant request failed.

Error behavior:

If HA raises `HomeAssistantError`, the function catches it and returns a structured failure result instead of raising an HTTP exception. This keeps `/commands` responses shaped like command results even when HA fails.

---

## `services/ha_service.py`

Purpose: Business wrapper for direct Home Assistant service calls.

### `call_service(domain, service, request)`

Runs a direct HA service call and optional verification.

Steps:

1. Copy `request.service_data`.
2. Add `request.entity_id` to service payload if provided.
3. Read state before the call when `entity_id` is a single string.
4. Call Home Assistant service with `ha_client.call_service()`.
5. Read state after the call when possible.
6. Compute expected state from service name or `request.expected_state`.
7. Verify state if `request.require_verification` is true.
8. Return call result and verification details.

Difference from `execute_command()`: this function is for direct `/services/{domain}/{service}` calls and does not use the full Hermes command envelope.

---

## `services/mock_device_service.py`

Purpose: Create, list, group, and control mock Home Assistant devices.

Mock devices are represented as HA states with special attributes.

### `build_mock_attributes(device)`

Builds the attribute dictionary stored in Home Assistant for a mock device.

Base attributes:

- `friendly_name`
- `supported_features`
- `mock_device: true`
- `managed_by: smart-home-ha-backend`
- `room`
- `domain`

Then it merges `device.attributes`, allowing custom fields like `device_type`.

### `create_or_update_mock_device(device)`

Creates or updates one mock device in HA by calling:

```text
ha_client.set_state(device.entity_id, device.initial_state, attributes)
```

Used by `POST /mock/devices` and startup seeding.

### `seed_default_mock_devices()`

Loops through `DEFAULT_MOCK_DEVICES` and creates/updates each one in Home Assistant.

Called during FastAPI startup by `main.py`.

Returns a list of HA state responses.

### `default_mock_devices_by_room()`

Groups the default mock device catalog by room.

Used by:

```text
GET /mock/rooms
```

Important: this reads from the local default catalog, not from HA live state. That makes the endpoint fast and stable even if HA is offline.

### `list_mock_devices()`

Reads all HA states and filters down to entities where:

```json
{"attributes": {"mock_device": true}}
```

Used by:

```text
GET /mock/devices
```

### `set_mock_device_power(entity_id, state)`

Sets a mock device to `on` or `off` by updating its HA state.

It derives:

- friendly name from entity ID.
- domain from entity ID prefix.

Then calls `ha_client.set_state()`.

### `toggle_mock_device(entity_id)`

Reads current state, computes the next power state, and writes it back.

Rule:

- current `on` -> next `off`
- anything else -> next `on`

---

## `services/default_devices.py`

Purpose: Persistent default mock device catalog.

### `DEFAULT_MOCK_DEVICES`

Tuple of `MockDeviceCreate` objects seeded at backend startup.

Current defaults:

| Room | Entity ID | Domain | Device type |
|---|---|---|---|
| bedroom | `light.mock_bedroom_lamp` | `light` | lamp |
| living_room | `light.mock_living_room_lamp` | `light` | lamp |
| kitchen | `switch.mock_kitchen_plug` | `switch` | plug |
| bathroom | `light.mock_bathroom_light` | `light` | ceiling light |

To add a persistent mock device, add another `MockDeviceCreate(...)` entry here, then restart the backend.

---

## `routers/commands.py`

Purpose: HTTP route for Hermes command requests.

### `router = APIRouter(prefix="/commands", tags=["commands"])`

All routes in this file start with `/commands` and appear in Swagger under the `commands` tag.

### `command(request)`

Endpoint:

```text
POST /commands
```

Accepts a `CommandRequest`, calls `execute_command()`, and returns the structured command result.

---

## `routers/devices.py`

Purpose: HTTP routes for HA state entities.

### `devices()`

Endpoint:

```text
GET /devices
```

Returns all Home Assistant states.

### `device(entity_id)`

Endpoint:

```text
GET /devices/{entity_id}
```

Returns one Home Assistant state.

### `update_device_legacy(entity_id, state, attributes=None)`

Endpoint:

```text
PUT /devices/{entity_id}?state=on
```

Backward-compatible state update endpoint. It uses query/body parameters rather than the newer `StateUpdate` JSON model.

### `update_device_state(entity_id, request)`

Endpoint:

```text
POST /devices/{entity_id}/state
```

Creates or updates one HA state using a JSON body.

### `delete_device(entity_id)`

Endpoint:

```text
DELETE /devices/{entity_id}
```

Deletes one HA state and returns HTTP `204 No Content`.

Error handling: every route catches `HomeAssistantError` and converts it with `ha_error_response()`.

---

## `routers/health.py`

Purpose: Service status and Home Assistant connectivity routes.

### `root()`

Endpoint:

```text
GET /
```

Returns backend identity, running status, architecture summary, and capability list.

### `ha_health()`

Endpoint:

```text
GET /ha/health
```

Calls Home Assistant API health endpoint and returns connected status if successful.

### `ha_config()`

Endpoint:

```text
GET /ha/config
```

Returns HA config metadata from `/api/config`.

---

## `routers/mock_devices.py`

Purpose: HTTP routes for mock device catalog and manual control.

### `mock_rooms()`

Endpoint:

```text
GET /mock/rooms
```

Returns default mock devices grouped by room.

### `mock_devices()`

Endpoint:

```text
GET /mock/devices
```

Returns live HA states marked with `mock_device: true`.

### `register_mock_device(device)`

Endpoint:

```text
POST /mock/devices
```

Creates or updates a mock device state in Home Assistant.

### `turn_on_mock_device(entity_id)`

Endpoint:

```text
POST /mock/devices/{entity_id}/turn_on
```

Sets mock device state to `on`.

### `turn_off_mock_device(entity_id)`

Endpoint:

```text
POST /mock/devices/{entity_id}/turn_off
```

Sets mock device state to `off`.

### `toggle_mock_device_route(entity_id)`

Endpoint:

```text
POST /mock/devices/{entity_id}/toggle
```

Reads current state and flips it between `on` and `off`.

---

## `routers/services.py`

Purpose: HTTP routes for direct Home Assistant services.

### `services()`

Endpoint:

```text
GET /services
```

Returns all HA service domains and actions.

### `services_by_domain(domain)`

Endpoint:

```text
GET /services/{domain}
```

Searches HA service list for a matching domain.

If found, returns that domain's service metadata.

If not found, returns HTTP `404`.

### `call_service(domain, service, request)`

Endpoint:

```text
POST /services/{domain}/{service}
```

Calls a Home Assistant service through `services/ha_service.py` and returns optional verification details.

---

## `tests/test_backend_api.py`

Purpose: Unit tests for backend routes and service behavior.

### `BackendApiTests.setUp()`

Creates a FastAPI `TestClient` for each test.

### `test_main_import_stays_thin_and_routers_are_split()`

Verifies:

- `main.py` stays small.
- each router module exposes a `router` object.

This protects the layered architecture from drifting back into a monolithic `main.py`.

### `test_root_exposes_service_capabilities()`

Checks `GET /` returns backend identity and includes `/commands` in capabilities.

### `test_default_mock_devices_include_multiple_rooms()`

Checks default mock catalog contains multiple expected rooms and devices.

### `test_command_request_turns_off_real_device_and_verifies()`

Mocks HA calls and verifies `/commands` can turn off a real device path through `ha_client.call_service()`.

### `test_command_request_turns_off_mock_device_via_state_api()`

Mocks HA calls and verifies mock devices are controlled through `ha_client.set_state()` instead of real service calls.

### `test_mock_rooms_endpoint_groups_default_devices_by_room()`

Checks `/mock/rooms` groups default devices by room without needing live HA state.

### `test_mock_turn_on_uses_state_api_for_virtual_device()`

Checks `/mock/devices/{entity_id}/turn_on` writes state through HA state API.

### `test_register_mock_device_creates_state_in_home_assistant()`

Checks `POST /mock/devices` creates a mock HA state.

---

# Extension guide

## Add a new API endpoint

1. Add route function in the correct `routers/*.py` file.
2. If it needs business logic, add function in `services/*.py`.
3. If it needs a request body, add Pydantic model in `schemas/ha.py`.
4. If it calls Home Assistant directly, add method/wrapper in `ha_client.py`.
5. Add a unit test in `tests/test_backend_api.py`.
6. Update `docs/HA_BACKEND_API.md` if it changes public API usage.

## Add a new persistent mock device

Edit:

```text
backend/services/default_devices.py
```

Add:

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

Then restart backend so startup seeding creates/updates it in HA.

## Add a real Home Assistant device

1. Pair the device in Home Assistant.
2. Find its `entity_id` in Home Assistant Developer Tools -> States.
3. Use that entity ID in `/commands` or `/services/{domain}/{service}`.
4. Keep mock devices for testing even after real devices exist.

## Where to put future logic

| If you are adding... | Put it in... |
|---|---|
| New HTTP endpoint | `routers/` |
| Command/business workflow | `services/` |
| Request/response body | `schemas/` |
| Shared helper | `core/` |
| Raw HA REST call | `ha_client.py` |
| Default virtual room/device | `services/default_devices.py` |
| Public docs/API examples | `docs/HA_BACKEND_API.md` |
| Code/function explanations | `docs/BACKEND_CODE_GUIDE.md` |

---

# Common maintenance notes

## Mock vs real devices

Mock devices use HA state updates:

```text
POST /api/states/{entity_id}
```

Real devices use HA service calls:

```text
POST /api/services/{domain}/{service}
```

The backend hides this difference inside `execute_command()` so Hermes can use one command schema.

## Verification limitations

Current verification checks immediate HA state after the command. It works well for simple `turn_on` / `turn_off` flows.

Future improvements could add:

- retries using `max_retries`
- polling until `verify_timeout_sec`
- richer expected states for `toggle`, brightness, temperature, covers, locks, etc.

## Safety fields

`CommandRequest.safety` is currently accepted and returned as metadata, but not deeply enforced yet. Future safety enforcement should happen in `services/command_service.py` before calling Home Assistant.

## Secrets rule

Never put actual `HA_TOKEN`, `.env` contents, Home Assistant `.storage` auth data, or raw private state dumps in documentation.
