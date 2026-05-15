# Project Tree

_Last updated: 2026-05-15 16:54 ADT_

```text
.
├── .github/
│   ├── scripts/
│   │   └── check_html_scripts.py
│   └── workflows/
│       └── ci.yml
├── backend/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── errors.py
│   │   ├── logging.py
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
│   │   ├── mock_action_helpers.py
│   │   ├── mock_catalog.py
│   │   └── mock_device_service.py
│   ├── tests/
│   │   └── test_backend_api.py
│   ├── .dockerignore
│   ├── ha_client.py
│   ├── main.py
│   └── requirements.txt
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
│   ├── PROJECT_HEALTH_CHECK.md
│   ├── PROJECT_TREE.md
│   └── SMART_HOME_API_DOCS.html
├── .dockerignore
├── .gitignore
├── AGENT.md
├── docker-compose.yml
└── README.md
```

Notes:
- Home Assistant runtime/auth internals under `config/.storage/` are intentionally excluded from this tree.
