import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from services.default_devices import DEFAULT_MOCK_DEVICES


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_main_import_stays_thin_and_routers_are_split(self):
        import inspect
        import main
        from routers import commands, devices, health, mock_devices, services as services_router

        self.assertLessEqual(len(inspect.getsource(main).splitlines()), 60)
        self.assertTrue(hasattr(commands, "router"))
        self.assertTrue(hasattr(devices, "router"))
        self.assertTrue(hasattr(health, "router"))
        self.assertTrue(hasattr(mock_devices, "router"))
        self.assertTrue(hasattr(services_router, "router"))

    def test_root_exposes_service_capabilities(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["service"], "smart-home-ha-backend")
        self.assertIn("/commands", payload["capabilities"])

    def test_home_assistant_settings_prefer_ha_env_names(self):
        from ha_client import HomeAssistantSettings

        with patch.dict(
            "os.environ",
            {
                "HA_URL": "http://orin-ha:8123",
                "HA_TOKEN": "new-token",
                "HA_TIMEOUT_SEC": "7",
                "HASS_URL": "http://old-ha:8123",
                "HASS_TOKEN": "old-token",
                "HASS_TIMEOUT_SEC": "3",
            },
            clear=False,
        ):
            settings = HomeAssistantSettings.from_env()

        self.assertEqual(settings.url, "http://orin-ha:8123")
        self.assertEqual(settings.token, "new-token")
        self.assertEqual(settings.timeout_sec, 7.0)

    def test_home_assistant_settings_fall_back_to_hass_env_names(self):
        from ha_client import HomeAssistantSettings

        with patch.dict(
            "os.environ",
            {
                "HASS_URL": "http://fallback-ha:8123",
                "HASS_TOKEN": "fallback-token",
                "HASS_TIMEOUT_SEC": "5",
            },
            clear=True,
        ):
            settings = HomeAssistantSettings.from_env()

        self.assertEqual(settings.url, "http://fallback-ha:8123")
        self.assertEqual(settings.token, "fallback-token")
        self.assertEqual(settings.timeout_sec, 5.0)

    def test_default_mock_devices_include_multiple_rooms(self):
        room_names = {device.room for device in DEFAULT_MOCK_DEVICES}
        entity_ids = {device.entity_id for device in DEFAULT_MOCK_DEVICES}

        self.assertIn("bedroom", room_names)
        self.assertIn("living_room", room_names)
        self.assertIn("kitchen", room_names)
        self.assertIn("light.mock_bedroom_lamp", entity_ids)
        self.assertIn("light.mock_living_room_lamp", entity_ids)
        self.assertIn("switch.mock_kitchen_plug", entity_ids)

    @patch("services.action_service.ha_client")
    def test_command_request_turns_off_real_device_and_verifies(self, mock_ha):
        mock_ha.call_service.return_value = {"changed_states": []}
        mock_ha.get_state.side_effect = [
            {"entity_id": "light.real_bedroom_lamp", "state": "on", "attributes": {}},
            {"entity_id": "light.real_bedroom_lamp", "state": "off", "attributes": {}},
        ]

        response = self.client.post(
            "/commands",
            json={
                "schema_version": "ha-bridge.v1",
                "message_type": "ha.command.request",
                "request_id": "req_test_1",
                "intent": {
                    "domain": "light",
                    "service": "turn_off",
                    "entity_id": "light.real_bedroom_lamp",
                },
                "execution_policy": {"require_verification": True},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["message_type"], "ha.command.result")
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["verification"]["verified"])
        mock_ha.call_service.assert_called_once()

    @patch("services.action_service.ha_client")
    def test_command_request_turns_off_mock_device_via_state_api(self, mock_ha):
        mock_ha.get_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "on",
            "attributes": {"mock_device": True},
        }
        mock_ha.set_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "off",
            "attributes": {"mock_device": True},
        }

        response = self.client.post(
            "/commands",
            json={
                "schema_version": "ha-bridge.v1",
                "message_type": "ha.command.request",
                "request_id": "req_test_mock_1",
                "intent": {
                    "domain": "light",
                    "service": "turn_off",
                    "entity_id": "light.mock_bedroom_lamp",
                },
                "execution_policy": {"require_verification": True},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["verification"]["verified"])
        mock_ha.set_state.assert_called_once()
        mock_ha.call_service.assert_not_called()

    @patch("services.action_service.ha_client")
    def test_services_endpoint_reuses_canonical_mock_power_path(self, mock_ha):
        mock_ha.get_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "on",
            "attributes": {"mock_device": True},
        }
        mock_ha.set_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "off",
            "attributes": {"mock_device": True},
        }

        response = self.client.post(
            "/services/light/turn_off",
            json={"entity_id": "light.mock_bedroom_lamp", "require_verification": True},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertTrue(payload["verification"]["verified"])
        mock_ha.set_state.assert_called_once()
        mock_ha.call_service.assert_not_called()

    @patch("services.mock_device_service.ha_client")
    def test_mock_rooms_endpoint_groups_default_devices_by_room(self, mock_ha):
        response = self.client.get("/mock/rooms")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("bedroom", payload)
        self.assertIn("living_room", payload)
        self.assertIn("kitchen", payload)
        self.assertEqual(payload["bedroom"][0]["entity_id"], "light.mock_bedroom_lamp")
        mock_ha.get_states.assert_not_called()

    @patch("services.action_service.ha_client")
    def test_mock_turn_on_uses_state_api_for_virtual_device(self, mock_ha):
        mock_ha.get_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "off",
            "attributes": {"mock_device": True},
        }
        mock_ha.set_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "on",
            "attributes": {"friendly_name": "Mock Bedroom Lamp"},
        }

        response = self.client.post("/mock/devices/light.mock_bedroom_lamp/turn_on")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["entity_id"], "light.mock_bedroom_lamp")
        self.assertEqual(payload["state"], "on")
        mock_ha.set_state.assert_called_once()

    @patch("services.action_service.ha_client")
    def test_mock_toggle_computes_expected_state_and_verifies(self, mock_ha):
        mock_ha.get_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "on",
            "attributes": {"mock_device": True},
        }
        mock_ha.set_state.return_value = {
            "entity_id": "light.mock_bedroom_lamp",
            "state": "off",
            "attributes": {"mock_device": True},
        }

        response = self.client.post(
            "/services/light/toggle",
            json={"entity_id": "light.mock_bedroom_lamp", "require_verification": True},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["verification"]["expected_state"], "off")
        self.assertTrue(payload["verification"]["verified"])

    @patch("services.action_service.ha_client")
    def test_mock_endpoint_rejects_non_mock_entities(self, mock_ha):
        mock_ha.get_state.return_value = {
            "entity_id": "light.real_bedroom_lamp",
            "state": "off",
            "attributes": {},
        }

        response = self.client.post("/mock/devices/light.real_bedroom_lamp/turn_on")

        self.assertEqual(response.status_code, 404)
        mock_ha.set_state.assert_not_called()
        mock_ha.call_service.assert_not_called()

    @patch("services.action_service.ha_client")
    def test_unverifiable_service_call_reports_verification_not_performed(self, mock_ha):
        mock_ha.call_service.return_value = {"changed_states": []}

        response = self.client.post(
            "/services/homeassistant/restart",
            json={"require_verification": True},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertFalse(payload["verification"]["performed"])
        self.assertIsNone(payload["verification"]["verified"])

    @patch("services.mock_device_service.ha_client")
    def test_register_mock_device_creates_state_in_home_assistant(self, mock_ha):
        mock_ha.set_state.return_value = {
            "entity_id": "light.test_lamp",
            "state": "off",
            "attributes": {"friendly_name": "Test Lamp"},
        }

        response = self.client.post(
            "/mock/devices",
            json={
                "entity_id": "light.test_lamp",
                "name": "Test Lamp",
                "domain": "light",
                "room": "test_room",
                "initial_state": "off",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["entity_id"], "light.test_lamp")
        self.assertEqual(payload["state"], "off")
        mock_ha.set_state.assert_called_once()


if __name__ == "__main__":
    unittest.main()
