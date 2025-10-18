#!/usr/bin/env python3

import json
import logging
import os
import queue
import sys
import threading
import time
from urllib.parse import urlparse, urlunparse

import requests
from flask import Flask, Response, jsonify, request
from flask_sock import Sock

# Configure logging with optional override via environment variable
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Suppress Werkzeug request logs

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))


app = Flask(__name__)
app.config['SECRET_KEY'] = 'everything-presence-configurator-secret'
sock = Sock(app)

SUPERVISOR_TOKEN = os.getenv('SUPERVISOR_TOKEN')
HA_URL = os.getenv('HA_URL')
HA_TOKEN = os.getenv('HA_TOKEN')

if SUPERVISOR_TOKEN:
    HOME_ASSISTANT_API = 'http://supervisor/core/api'
    headers = {
        'Authorization': f'Bearer {SUPERVISOR_TOKEN}',
        'Content-Type': 'application/json',
    }
elif HA_URL and HA_TOKEN:
    HOME_ASSISTANT_API = HA_URL.rstrip('/') + '/api'
    headers = {
        'Authorization': f'Bearer {HA_TOKEN}',
        'Content-Type': 'application/json',
    }
else:
    logger.error('No SUPERVISOR_TOKEN found and no HA_URL and HA_TOKEN provided.')
    sys.exit(1)


def get_ha_websocket_url(home_assistant_api: str, supervisor_token: str | None) -> str:
    """Return the Home Assistant WebSocket endpoint."""
    if supervisor_token:
        return 'ws://supervisor/core/websocket'

    if not home_assistant_api:
        raise ValueError('Home Assistant API URL is required when no supervisor token is present.')

    parsed = urlparse(home_assistant_api)
    scheme = 'wss' if parsed.scheme == 'https' else 'ws'
    base_path = parsed.path.rstrip('/')
    if base_path.endswith('/api'):
        base_path = base_path[:-4]
    websocket_path = f"{base_path}/api/websocket"
    return urlunparse((scheme, parsed.netloc, websocket_path or '/api/websocket', '', '', ''))


def build_auth_message(supervisor_token: str | None, ha_token: str | None) -> dict | None:
    """Return the authentication message for the Home Assistant WebSocket."""
    if supervisor_token:
        logger.info('Authenticating Home Assistant WebSocket using Supervisor token')
        return {
            'type': 'auth',
            'access_token': supervisor_token
        }

    if ha_token:
        logger.info('Authenticating Home Assistant WebSocket using Home Assistant token')
        return {
            'type': 'auth',
            'access_token': ha_token
        }

    logger.error('No authentication token available for Home Assistant WebSocket connection')
    return None


def should_forward_state_change(entity_id: str, selected_entities: set[str]) -> bool:
    """Determine whether a state change event should be forwarded to the frontend."""
    if not entity_id:
        logger.debug('Ignoring state_changed event with missing entity_id')
        return False

    if selected_entities:
        if entity_id in selected_entities:
            logger.info('Forwarding state_changed event for %s', entity_id)
            return True
        logger.debug('Ignoring state_changed event for %s (not selected)', entity_id)
        return False

    if is_mmwave_entity(entity_id):
        logger.info('Forwarding mmWave state_changed event for %s (no selected entities)', entity_id)
        return True

    logger.debug('Ignoring state_changed event for %s (no selected entities)', entity_id)
    return False


def check_connectivity():
    """Function to check connectivity with Home Assistant API."""
    logger.debug('Checking connectivity to Home Assistant API at %s', HOME_ASSISTANT_API)
    try:
        response = requests.get(f'{HOME_ASSISTANT_API}/', headers=headers, timeout=10)

        if response.status_code != 200:
            logger.error('Failed to connect to Home Assistant API. Status Code: %s', response.status_code)
            logger.debug('Response snippet: %s', response.text[:200])
        else:
            logger.info('Successfully connected to Home Assistant API (status %s)', response.status_code)
    except requests.exceptions.RequestException as exc:
        logger.error('Exception connecting to Home Assistant API: %s', exc)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to test HA connectivity"""
    try:
        logger.debug('Health check requested')
        response = requests.get(f'{HOME_ASSISTANT_API}/', headers=headers, timeout=5)

        return jsonify({
            "backend_status": "running",
            "ha_api_url": f"{HOME_ASSISTANT_API}/",
            "ha_response_status": response.status_code,
            "ha_response_type": response.headers.get('Content-Type', 'unknown'),
            "supervisor_token_available": bool(SUPERVISOR_TOKEN),
            "ha_url_override": bool(HA_URL),
            "ha_token_override": bool(HA_TOKEN)
        })
    except Exception as exc:
        logger.exception('Health check failed: %s', exc)
        return jsonify({
            "backend_status": "running",
            "error": str(exc),
            "ha_api_url": f"{HOME_ASSISTANT_API}/",
            "supervisor_token_available": bool(SUPERVISOR_TOKEN),
            "ha_url_override": bool(HA_URL),
            "ha_token_override": bool(HA_TOKEN)
        }), 500


@app.route('/api/template', methods=['POST'])
def execute_template():
    """Forward a Jinja2 template to Home Assistant for evaluation."""
    data = request.get_json()
    template = data.get('template') if isinstance(data, dict) else None
    if not template:
        return jsonify({"error": "No template provided"}), 400

    try:
        response = requests.post(
            f'{HOME_ASSISTANT_API}/template',
            headers=headers,
            json={"template": template},
            timeout=10
        )

        if response.status_code == 200:
            return Response(response.content, status=200, content_type=response.headers.get('Content-Type', 'application/json'))

        logger.error('Failed to execute template. Status Code: %s', response.status_code)
        return jsonify({
            "error": f"HA API returned {response.status_code}",
            "details": response.text[:200],
            "content_type": response.headers.get('Content-Type', 'unknown')
        }), response.status_code
    except requests.exceptions.ConnectionError as exc:
        logger.error('Connection error to HA API: %s', exc)
        return jsonify({"error": "Cannot connect to Home Assistant API", "details": str(exc)}), 502
    except requests.exceptions.Timeout as exc:
        logger.error('Timeout connecting to HA API: %s', exc)
        return jsonify({"error": "Timeout connecting to Home Assistant API", "details": str(exc)}), 504
    except Exception as exc:
        logger.exception('Exception occurred while executing template: %s', exc)
        return jsonify({"error": "Exception occurred while executing template", "details": str(exc)}), 500


missing_entity_warnings: set[str] = set()


@app.route('/api/entities/<entity_id>', methods=['GET'])
def get_entity_state(entity_id):
    """Endpoint to get the state of a specific entity."""
    global missing_entity_warnings

    response = requests.get(f'{HOME_ASSISTANT_API}/states/{entity_id}', headers=headers)
    if response.status_code == 200:
        if entity_id in missing_entity_warnings:
            logger.info('Entity %s is now available', entity_id)
            missing_entity_warnings.discard(entity_id)
        return jsonify(response.json())

    if response.status_code == 404:
        if entity_id not in missing_entity_warnings:
            logger.info('Home Assistant reports %s is unavailable (404); continuing without it', entity_id)
            missing_entity_warnings.add(entity_id)
        return jsonify({'error': 'Entity not found'}), 404

    logger.warning('Failed to fetch entity %s: status %s', entity_id, response.status_code)
    return jsonify({'error': 'Unauthorized or entity not found'}), response.status_code


@app.route('/api/services/number/set_value', methods=['POST'])
def set_value():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')
        value = data.get('value')

        if not entity_id or value is None:
            return jsonify({"error": "Missing entity_id or value"}), 400

        payload = {
            "entity_id": entity_id,
            "value": value
        }

        response = requests.post(f'{HOME_ASSISTANT_API}/services/number/set_value', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Updated %s to value %s', entity_id, value)
            return jsonify({"message": f"Entity {entity_id} updated successfully."}), 200

        logger.error('Failed to update %s via number.set_value: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to update entity {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while setting value for %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while setting the value.", "details": str(exc)}), 500


@app.route('/api/services/switch/turn_on', methods=['POST'])
def switch_turn_on():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        payload = {"entity_id": entity_id}
        response = requests.post(f'{HOME_ASSISTANT_API}/services/switch/turn_on', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Switch %s turned on', entity_id)
            return jsonify({"message": f"Switch {entity_id} turned on successfully."}), 200

        logger.error('Failed to turn on switch %s: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to turn on switch {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while turning on switch %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while turning on the switch.", "details": str(exc)}), 500


@app.route('/api/services/switch/turn_off', methods=['POST'])
def switch_turn_off():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        payload = {"entity_id": entity_id}
        response = requests.post(f'{HOME_ASSISTANT_API}/services/switch/turn_off', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Switch %s turned off', entity_id)
            return jsonify({"message": f"Switch {entity_id} turned off successfully."}), 200

        logger.error('Failed to turn off switch %s: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to turn off switch {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while turning off switch %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while turning off the switch.", "details": str(exc)}), 500


@app.route('/api/services/select/select_option', methods=['POST'])
def select_option():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')
        option = data.get('option')

        if not entity_id or option is None:
            return jsonify({"error": "Missing entity_id or option"}), 400

        payload = {
            "entity_id": entity_id,
            "option": option
        }

        response = requests.post(f'{HOME_ASSISTANT_API}/services/select/select_option', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Select %s updated to %s', entity_id, option)
            return jsonify({"message": f"Select entity {entity_id} updated successfully."}), 200

        logger.error('Failed to update select %s: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to update select entity {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while updating select %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while updating the select entity.", "details": str(exc)}), 500


@app.route('/api/services/light/turn_on', methods=['POST'])
def light_turn_on():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        payload = {"entity_id": entity_id}
        response = requests.post(f'{HOME_ASSISTANT_API}/services/light/turn_on', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Light %s turned on', entity_id)
            return jsonify({"message": f"Light {entity_id} turned on successfully."}), 200

        logger.error('Failed to turn on light %s: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to turn on light {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while turning on light %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while turning on the light.", "details": str(exc)}), 500


@app.route('/api/services/light/turn_off', methods=['POST'])
def light_turn_off():
    try:
        data = request.json or {}
        entity_id = data.get('entity_id')

        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400

        payload = {"entity_id": entity_id}
        response = requests.post(f'{HOME_ASSISTANT_API}/services/light/turn_off', headers=headers, json=payload)

        if response.status_code == 200:
            logger.info('Light %s turned off', entity_id)
            return jsonify({"message": f"Light {entity_id} turned off successfully."}), 200

        logger.error('Failed to turn off light %s: %s', entity_id, response.text)
        return jsonify({"error": f"Failed to turn off light {entity_id}.", "details": response.text}), response.status_code

    except Exception as exc:
        logger.exception('Error while turning off light %s: %s', entity_id if 'entity_id' in locals() else 'unknown', exc)
        return jsonify({"error": "An error occurred while turning off the light.", "details": str(exc)}), 500


# Removed unused /api/supervisor/token route - no longer needed with backend WebSocket proxy
# Removed unused /api/test-websocket route - debugging endpoint no longer needed

# Global set to store currently selected entities for WebSocket filtering
selected_entity_ids = set()


@app.route('/api/selected-entities', methods=['POST'])
def set_selected_entities():
    """Set the list of entities that the frontend is currently interested in"""
    global selected_entity_ids
    try:
        data = request.get_json(silent=True) or {}
        entity_ids = data.get('entity_ids', [])
        selected_entity_ids = set(entity_ids)
        logger.info('Updated selected entities list (%s items)', len(selected_entity_ids))
        return jsonify({'success': True, 'count': len(selected_entity_ids)})
    except Exception as exc:
        logger.exception('Error setting selected entities: %s', exc)
        return jsonify({'error': str(exc)}), 500


@app.route('/api/selected-entities', methods=['GET'])
def get_selected_entities():
    """Get the current list of selected entities"""
    global selected_entity_ids
    return jsonify({'entity_ids': list(selected_entity_ids), 'count': len(selected_entity_ids)})


def is_mmwave_entity(entity_id):
    """Check if an entity is related to mmWave sensors using the same logic as frontend"""
    if not entity_id:
        return False

    required_suffixes = [
        # Zone Coordinates
        "zone_1_begin_x", "zone_1_begin_y", "zone_1_end_x", "zone_1_end_y",
        "zone_2_begin_x", "zone_2_begin_y", "zone_2_end_x", "zone_2_end_y",
        "zone_3_begin_x", "zone_3_begin_y", "zone_3_end_x", "zone_3_end_y",
        "zone_4_begin_x", "zone_4_begin_y", "zone_4_end_x", "zone_4_end_y",

        # Target Tracking
        "target_1_active", "target_2_active", "target_3_active",

        # Target Coordinates and Attributes
        "target_1_x", "target_1_y", "target_1_speed", "target_1_resolution",
        "target_2_x", "target_2_y", "target_2_speed", "target_2_resolution",
        "target_3_x", "target_3_y", "target_3_speed", "target_3_resolution",

        # Target Angles and Distances
        "target_1_angle", "target_2_angle", "target_3_angle",
        "target_1_distance", "target_2_distance", "target_3_distance",

        # Zone Occupancy Off Delay
        "zone_1_occupancy_off_delay", "zone_2_occupancy_off_delay",
        "zone_3_occupancy_off_delay", "zone_4_occupancy_off_delay",

        # Configured Values
        "max_distance", "installation_angle",

        # Occupancy Masks (Exclusion Zones)
        "occupancy_mask_1_begin_x", "occupancy_mask_1_begin_y",
        "occupancy_mask_1_end_x", "occupancy_mask_1_end_y",
        "occupancy_mask_2_begin_x", "occupancy_mask_2_begin_y",
        "occupancy_mask_2_end_x", "occupancy_mask_2_end_y",

        # Settings Entities
        "bluetooth_switch", "inverse_mounting", "aggressive_target_clearing",
        "off_delay", "zone_1_off_delay", "zone_2_off_delay", "zone_3_off_delay", "zone_4_off_delay",
        "aggressive_timeout", "illuminance_offset_ui", "illuminance_offset",
        "esp32_led", "status_led",
    ]

    return any(entity_id.endswith(suffix) for suffix in required_suffixes)


@sock.route('/ws')
def websocket_proxy(ws):
    """WebSocket proxy to Home Assistant WebSocket API"""
    import websocket

    to_ha_queue: queue.Queue[str] = queue.Queue()
    from_ha_queue: queue.Queue[str] = queue.Queue()
    ha_ws = None
    proxy_active = True
    connection_ready = threading.Event()

    def ha_on_open(ha_ws_instance):
        logger.info('Home Assistant WebSocket connection opened')
        connection_ready.clear()
        auth_message = build_auth_message(SUPERVISOR_TOKEN, HA_TOKEN)
        if auth_message:
            try:
                ha_ws_instance.send(json.dumps(auth_message))
                logger.debug('Sent authentication payload to Home Assistant WebSocket')
            except Exception as exc:
                logger.error('Failed to send authentication payload: %s', exc)
        else:
            logger.error('No authentication payload available, closing Home Assistant WebSocket')
            ha_ws_instance.close()

    def ha_on_message(ha_ws_instance, message):
        nonlocal proxy_active
        global selected_entity_ids
        try:
            data = json.loads(message) if isinstance(message, str) else message
        except Exception as exc:
            logger.warning('Received non-JSON message from Home Assistant: %s', exc)
            from_ha_queue.put(message)
            return

        message_type = data.get('type')
        if message_type == 'auth_required':
            logger.debug('Home Assistant WebSocket requested authentication')
            return
        if message_type == 'auth_ok':
            logger.info('Authenticated with Home Assistant WebSocket')
            connection_ready.set()
            return
        if message_type == 'auth_invalid':
            logger.error('Home Assistant WebSocket rejected authentication: %s', data)
            proxy_active = False
            connection_ready.clear()
            return

        if message_type == 'result':
            if not data.get('success') and 'id' in data:
                error_info = data.get('error', {})
                logger.error('HA subscription failed for ID %s: %s', data.get('id'), error_info)
            result_data = data.get('result', [])
            if isinstance(result_data, list):
                filtered_entities = [
                    entity for entity in result_data
                    if should_forward_state_change(
                        entity.get('entity_id', ''), selected_entity_ids
                    )
                ]
                if filtered_entities:
                    filtered_data = dict(data)
                    filtered_data['result'] = filtered_entities
                    from_ha_queue.put(json.dumps(filtered_data))
                return

        if message_type == 'event':
            event_data = data.get('event', {})
            if event_data.get('event_type') == 'state_changed':
                entity_id = event_data.get('data', {}).get('entity_id', '')
                if should_forward_state_change(entity_id, selected_entity_ids):
                    from_ha_queue.put(message if isinstance(message, str) else json.dumps(data))
                return

        # Forward any other message types unchanged
        from_ha_queue.put(message if isinstance(message, str) else json.dumps(data))

    def ha_on_error(ha_ws_instance, error):
        logger.error('HA WebSocket error: %s', error)
        connection_ready.clear()

    def ha_on_close(ha_ws_instance, close_status_code, close_msg):
        nonlocal proxy_active
        if close_status_code and close_status_code != 1000:
            logger.error('HA WebSocket closed unexpectedly: %s - %s', close_status_code, close_msg)
        else:
            logger.info('HA WebSocket closed (code %s)', close_status_code)
        proxy_active = False
        connection_ready.clear()

    ha_websocket_url = get_ha_websocket_url(HOME_ASSISTANT_API, SUPERVISOR_TOKEN)
    logger.info('Connecting to Home Assistant WebSocket at %s', ha_websocket_url)
    ha_ws = websocket.WebSocketApp(
        ha_websocket_url,
        on_open=ha_on_open,
        on_message=ha_on_message,
        on_error=ha_on_error,
        on_close=ha_on_close
    )

    ha_thread = threading.Thread(target=ha_ws.run_forever)
    ha_thread.daemon = True
    ha_thread.start()

    def forward_to_ha():
        while proxy_active and ha_thread.is_alive():
            try:
                message = to_ha_queue.get(timeout=1)
            except queue.Empty:
                continue

            if not proxy_active:
                break

            if not connection_ready.wait(timeout=5):
                logger.warning('Home Assistant WebSocket not ready after waiting 5s; will retry message')
                if proxy_active:
                    to_ha_queue.put(message)
                    time.sleep(1)
                continue

            if ha_ws and ha_ws.sock and ha_ws.sock.connected:
                try:
                    ha_ws.send(message)
                    logger.debug('Forwarded message from frontend to Home Assistant (%s bytes)', len(message))
                except Exception as exc:
                    logger.error('Error forwarding message to Home Assistant: %s', exc)
                    if proxy_active:
                        to_ha_queue.put(message)
                        time.sleep(1)
            else:
                logger.warning('Home Assistant WebSocket not connected; message will be retried')
                if proxy_active:
                    to_ha_queue.put(message)
                    time.sleep(1)

    forward_thread = threading.Thread(target=forward_to_ha)
    forward_thread.daemon = True
    forward_thread.start()

    try:
        while proxy_active:
            try:
                while not from_ha_queue.empty():
                    ha_message = from_ha_queue.get_nowait()
                    ws.send(ha_message)
            except queue.Empty:
                pass
            except Exception as exc:
                logger.error('Error sending to frontend: %s', exc)
                break

            try:
                frontend_message = ws.receive(timeout=0.1)
                if frontend_message:
                    logger.debug('Received message from frontend (%s bytes)', len(frontend_message))
                    to_ha_queue.put(frontend_message)
            except Exception as exc:
                message_text = str(exc).lower()
                if 'timeout' not in message_text and 'connection closed: 1000' not in message_text:
                    logger.error('Error receiving from frontend: %s', exc)
                break
    except Exception as exc:
        logger.error('WebSocket proxy error: %s', exc)
    finally:
        proxy_active = False
        connection_ready.clear()
        if ha_ws:
            try:
                ha_ws.close()
            except Exception as exc:
                logger.debug('Error while closing Home Assistant WebSocket: %s', exc)


if __name__ == '__main__':
    threading.Thread(target=check_connectivity, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
