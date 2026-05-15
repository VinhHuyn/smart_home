# Project Tree

_Last updated: 2026-05-15 03:25_

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
│   │   ├── action_service.py
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
│   ├── .HA_VERSION
│   ├── automations.yaml
│   ├── configuration.yaml
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
│   ├── PROJECT_DOC.md
│   ├── PROJECT_TREE.md
│   └── SMART_HOME_API_DOCS.html
├── .gitignore
├── AGENT.md
└── docker-compose.yml
```
