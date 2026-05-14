# Project Tree

_Last updated: 2026-05-14 14:48_

```text
.
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   └── time.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── commands.py
│   │   ├── devices.py
│   │   ├── health.py
│   │   ├── mock_devices.py
│   │   └── services.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── ha.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── command_service.py
│   │   ├── default_devices.py
│   │   ├── ha_service.py
│   │   └── mock_device_service.py
│   ├── tests/
│   │   └── test_backend_api.py
│   ├── .gitignore
│   ├── ha_client.py
│   ├── main.py
│   ├── project.code-workspace
│   ├── README.md
│   └── requirements.txt
├── config/
│   ├── .cloud/
│   ├── .storage/
│   │   ├── assist_pipeline.pipelines
│   │   ├── auth
│   │   ├── auth_provider.homeassistant
│   │   ├── bluetooth.passive_update_processor
│   │   ├── core.analytics
│   │   ├── core.area_registry
│   │   ├── core.config
│   │   ├── core.config_entries
│   │   ├── core.device_registry
│   │   ├── core.entity_registry
│   │   ├── core.restore_state
│   │   ├── core.uuid
│   │   ├── frontend.system_data
│   │   ├── frontend.user_data_71d1ed7bd36743059ab5c39dc805bf0f
│   │   ├── homeassistant.exposed_entities
│   │   ├── http
│   │   ├── http.auth
│   │   ├── lovelace.map
│   │   ├── lovelace_dashboards
│   │   ├── onboarding
│   │   ├── person
│   │   ├── repairs.issue_registry
│   │   └── trace.saved_traces
│   ├── blueprints/
│   │   ├── automation/
│   │   │   └── homeassistant/
│   │   │       ├── motion_light.yaml
│   │   │       └── notify_leaving_zone.yaml
│   │   └── script/
│   │       └── homeassistant/
│   │           └── confirmable_notification.yaml
│   ├── deps/
│   ├── tts/
│   ├── .ha_run.lock
│   ├── .HA_VERSION
│   ├── automations.yaml
│   ├── configuration.yaml
│   ├── home-assistant_v2.db
│   ├── home-assistant_v2.db-shm
│   ├── home-assistant_v2.db-wal
│   ├── scenes.yaml
│   └── scripts.yaml
├── docs/
│   ├── wiki/
│   │   ├── concepts/
│   │   │   └── documentation-sync.md
│   │   ├── entities/
│   │   │   └── smart-home-project.md
│   │   ├── queries/
│   │   │   └── doc-sync-runs.md
│   │   ├── index.md
│   │   ├── log.md
│   │   └── SCHEMA.md
│   ├── BACKEND_CODE_GUIDE.md
│   ├── CHANGELOG.md
│   ├── HA_BACKEND_API.md
│   └── PROJECT_TREE.md
├── AGENT.md
└── docker-compose.yml
```
