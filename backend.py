#!/usr/bin/env python3

from flask import Flask, jsonify, request, Response
from flask_sock import Sock
import requests
import os
import logging
import threading
import sys
import time
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG for easier debugging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Suppress Werkzeug request logs

app = Flask(__name__, static_folder='www', static_url_path='')
app.secret_key = os.environ.get("SESSION_SECRET", "sense-360-configurator-secret")
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
    logging.error('No SUPERVISOR_TOKEN found and no HA_URL and HA_TOKEN provided.')
    logging.error('This application requires Home Assistant API credentials to function.')
    sys.exit(1)

def check_connectivity():
    """Function to check connectivity with Home Assistant API."""
    try:
        response = requests.get(f'{HOME_ASSISTANT_API}/', headers=headers, timeout=10)
        if response.status_code != 200:
            logging.error(f"Failed to connect to Home Assistant API. Status Code: {response.status_code}")
            logging.error(f"Response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Exception connecting to Home Assistant API: {e}")



# Serve the main HTML file
@app.route('/')
def index():
    """Serve the main HTML file"""
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to test HA connectivity"""
    try:
        logging.debug("🩺 Health check requested")
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
    except Exception as e:
        return jsonify({
            "backend_status": "running",
            "error": str(e),
            "ha_api_url": f"{HOME_ASSISTANT_API}/",
            "supervisor_token_available": bool(SUPERVISOR_TOKEN),
            "ha_url_override": bool(HA_URL),
            "ha_token_override": bool(HA_TOKEN)
        }), 500

@app.route('/api/template', methods=['POST'])
def execute_template():
    """
    Endpoint to execute a Jinja2 template by forwarding it to Home Assistant's /api/template endpoint.
    It acts as a proxy, forwarding the template and returning the rendered result.
    """
    data = request.get_json()
    template = data.get('template')
    
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
        else:
            logging.error(f"Failed to execute template. Status Code: {response.status_code}")
            return jsonify({
                "error": f"HA API returned {response.status_code}",
                "details": response.text[:200],
                "content_type": response.headers.get('Content-Type', 'unknown')
            }), response.status_code
            
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection error to HA API: {e}")
        return jsonify({"error": "Cannot connect to Home Assistant API", "details": str(e)}), 502
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout connecting to HA API: {e}")
        return jsonify({"error": "Timeout connecting to Home Assistant API", "details": str(e)}), 504
    except Exception as e:
        logging.error(f"Exception occurred while executing template: {e}")
        return jsonify({"error": "Exception occurred while executing template", "details": str(e)}), 500

missing_entity_warnings: set[str] = set()


@app.route('/api/entities/<entity_id>', methods=['GET'])
def get_entity_state(entity_id):
    """
    Endpoint to get the state of a specific entity.
    """
    global missing_entity_warnings

    response = requests.get(f'{HOME_ASSISTANT_API}/states/{entity_id}', headers=headers)
    if response.status_code == 200:
        if entity_id in missing_entity_warnings:
            logging.info('Entity %s is now available', entity_id)
            missing_entity_warnings.discard(entity_id)
        return jsonify(response.json())

    if response.status_code == 404:
        if entity_id not in missing_entity_warnings:
            logging.info('Home Assistant reports %s is unavailable (404); continuing without it', entity_id)
            missing_entity_warnings.add(entity_id)
        return jsonify({'error': 'Entity not found'}), 404

    logging.warning('Failed to fetch entity %s: status %s', entity_id, response.status_code)
    return jsonify({'error': 'Unauthorized or entity not found'}), response.status_code

@app.route('/api/services/number/set_value', methods=['POST'])
def set_value():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        value = data.get('value')
        
        if not entity_id or value is None:
            return jsonify({"error": "Missing entity_id or value"}), 400
        

        
        payload = {
            "entity_id": entity_id,
            "value": value
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/number/set_value', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Entity {entity_id} updated successfully."}), 200
        else:
            return jsonify({"error": f"Failed to update entity {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while setting the value.", "details": str(e)}), 500

@app.route('/api/services/switch/turn_on', methods=['POST'])
def switch_turn_on():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        
        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400
        
        payload = {
            "entity_id": entity_id
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/switch/turn_on', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Switch {entity_id} turned on successfully."}), 200
        else:
            return jsonify({"error": f"Failed to turn on switch {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while turning on the switch.", "details": str(e)}), 500

@app.route('/api/services/switch/turn_off', methods=['POST'])
def switch_turn_off():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        
        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400
        
        payload = {
            "entity_id": entity_id
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/switch/turn_off', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Switch {entity_id} turned off successfully."}), 200
        else:
            return jsonify({"error": f"Failed to turn off switch {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while turning off the switch.", "details": str(e)}), 500

@app.route('/api/services/select/select_option', methods=['POST'])
def select_option():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        option = data.get('option')
        
        if not entity_id or option is None:
            return jsonify({"error": "Missing entity_id or option"}), 400
        
        payload = {
            "entity_id": entity_id,
            "option": option
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/select/select_option', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Select entity {entity_id} updated successfully."}), 200
        else:
            return jsonify({"error": f"Failed to update select entity {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while updating the select entity.", "details": str(e)}), 500

@app.route('/api/services/light/turn_on', methods=['POST'])
def light_turn_on():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        
        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400
        
        payload = {
            "entity_id": entity_id
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/light/turn_on', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Light {entity_id} turned on successfully."}), 200
        else:
            return jsonify({"error": f"Failed to turn on light {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while turning on the light.", "details": str(e)}), 500

@app.route('/api/services/light/turn_off', methods=['POST'])
def light_turn_off():
    try:
        data = request.json
        entity_id = data.get('entity_id')
        
        if not entity_id:
            return jsonify({"error": "Missing entity_id"}), 400
        
        payload = {
            "entity_id": entity_id
        }
        
        # Make the POST request to Home Assistant API
        response = requests.post(f'{HOME_ASSISTANT_API}/services/light/turn_off', headers=headers, json=payload)
        
        if response.status_code == 200:
            return jsonify({"message": f"Light {entity_id} turned off successfully."}), 200
        else:
            return jsonify({"error": f"Failed to turn off light {entity_id}.", "details": response.text}), response.status_code
            
    except Exception as e:
        return jsonify({"error": "An error occurred while turning off the light.", "details": str(e)}), 500

# Global set to store currently selected entities for WebSocket filtering
selected_entity_ids = set()

@app.route('/api/selected-entities', methods=['POST'])
def set_selected_entities():
    """Set the list of entities that the frontend is currently interested in"""
    global selected_entity_ids
    try:
        data = request.get_json()
        entity_ids = data.get('entity_ids', [])
        selected_entity_ids = set(entity_ids)
        return jsonify({'success': True, 'count': len(selected_entity_ids)})
    except Exception as e:
        logging.error(f"Error setting selected entities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/selected-entities', methods=['GET'])
def get_selected_entities():
    """Get the current list of selected entities"""
    global selected_entity_ids
    return jsonify({'entity_ids': list(selected_entity_ids), 'count': len(selected_entity_ids)})

def is_mmwave_entity(entity_id):
    """Check if an entity is related to mmWave sensors using the same logic as frontend"""
    if not entity_id:
        return False
    
    # Use the same required suffixes as the frontend filterRequiredEntities function
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
    import json
    import threading
    import queue
    
    # Create communication queues
    to_ha_queue = queue.Queue()
    from_ha_queue = queue.Queue()
    ha_ws = None
    proxy_active = True
    
    def ha_on_open(ha_ws_instance):
        supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        if supervisor_token:
            auth_message = {
                "type": "auth",
                "access_token": supervisor_token
            }
            ha_ws_instance.send(json.dumps(auth_message))
        else:
            logging.error("No supervisor token available for WebSocket auth")
    
    def ha_on_message(ha_ws_instance, message):
        # Filter and forward HA messages to frontend
        global selected_entity_ids  # Must be declared at the beginning of the function
        try:
            # Parse message
            import json
            data = json.loads(message) if isinstance(message, str) else message
            
            # Handle authentication
            if data.get('type') == 'auth_required':
                return
            elif data.get('type') == 'auth_ok':
                return
            elif data.get('type') == 'auth_invalid':
                logging.error("HA WebSocket authentication failed")
                return
            
            # Filter state results to only selected device entities
            if data.get('type') == 'result' and data.get('success'):
                result_data = data.get('result', [])
                if isinstance(result_data, list):
                    # Filter entities to only mmWave related ones
                    filtered_result = []
                    for entity in result_data:
                        entity_id = entity.get('entity_id', '')
                        if is_mmwave_entity(entity_id):
                            filtered_result.append(entity)
                    data['result'] = filtered_result
            
            # Filter events to only include selected entities or mmWave entities
            elif data.get('type') == 'event':
                event_data = data.get('event', {})
                if event_data.get('event_type') == 'state_changed':
                    entity_id = event_data.get('data', {}).get('entity_id', '')
                    
                    # Only forward if it's a selected entity or mmWave entity
                    if not (entity_id in selected_entity_ids or is_mmwave_entity(entity_id)):
                        return
            
            # Forward the (possibly filtered) message to frontend
            ws.send(json.dumps(data))
            
        except Exception as e:
            logging.error(f"Error processing HA WebSocket message: {e}")
    
    def ha_on_error(ha_ws_instance, error):
        logging.error(f"HA WebSocket error: {error}")
    
    def ha_on_close(ha_ws_instance, close_status_code, close_msg):
        logging.debug("HA WebSocket connection closed")
        nonlocal proxy_active
        proxy_active = False
    
    # Start HA WebSocket connection
    def start_ha_websocket():
        nonlocal ha_ws
        supervisor_token = os.environ.get('SUPERVISOR_TOKEN')
        if supervisor_token:
            ha_ws_url = "ws://supervisor/core/websocket"
        else:
            ha_url = os.environ.get('HA_URL', 'http://homeassistant.local:8123')
            ha_ws_url = ha_url.replace('http://', 'ws://').replace('https://', 'wss://') + '/api/websocket'
        
        ha_ws = websocket.WebSocketApp(
            ha_ws_url,
            on_open=ha_on_open,
            on_message=ha_on_message,
            on_error=ha_on_error,
            on_close=ha_on_close
        )
        ha_ws.run_forever()
    
    # Start HA WebSocket in separate thread
    ha_thread = threading.Thread(target=start_ha_websocket)
    ha_thread.daemon = True
    ha_thread.start()
    
    # Forward messages from frontend to HA
    while proxy_active:
        try:
            message = ws.receive(timeout=1.0)
            if message and ha_ws:
                ha_ws.send(message)
        except:
            break
    
    # Clean up
    if ha_ws:
        ha_ws.close()

if __name__ == '__main__':
    check_connectivity()
    # Bind to 0.0.0.0 and port 5000 as per guidelines
    app.run(host='0.0.0.0', port=5000, debug=True)
