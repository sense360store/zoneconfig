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
logging.basicConfig(level=logging.ERROR)  # Set global logging level to ERROR
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Suppress Werkzeug request logs

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
    logging.error('No SUPERVISOR_TOKEN found and no HA_URL and HA_TOKEN provided.')
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to test HA connectivity"""
    try:
        logging.error("🩺 Health check requested")
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

@app.route('/api/entities/<entity_id>', methods=['GET'])
def get_entity_state(entity_id):
    """
    Endpoint to get the state of a specific entity.
    """
    response = requests.get(f'{HOME_ASSISTANT_API}/states/{entity_id}', headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
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

# Removed unused /api/supervisor/token route - no longer needed with backend WebSocket proxy

# Removed unused /api/test-websocket route - debugging endpoint no longer needed

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
        
        # Configuration  
        "zone_type", "sensitivity", "custom_mode", "end_delay",
        "custom_end_delay_presence_sensor_1", "custom_end_delay_presence_sensor_2",
        "custom_end_delay_presence_sensor_3",
        
        # Special Presence and Zone Settings
        "zone_1_occupancy", "zone_2_occupancy", "zone_3_occupancy", "zone_4_occupancy",
        "any_target_active", "distance_resolution", "angle_resolution",
        
        # Additional Controls
        "custom_unoccupied_to_occupied_delay", "custom_occupied_to_unoccupied_delay_presence_sensor_1",
        "custom_occupied_to_unoccupied_delay_presence_sensor_2", "custom_occupied_to_unoccupied_delay_presence_sensor_3",
        
        # Common LD2410 settings
        "max_distance_gate", "max_movement_distance_gate", "max_still_distance_gate",
        "timeout", "light_function", "out_pin_level"
    ]
    
    # Check if entity_id ends with any required suffix
    for suffix in required_suffixes:
        if entity_id.endswith(suffix):
            return True
    
    return False

@sock.route('/websocket')
def handle_websocket(sock):
    """WebSocket endpoint that streams Home Assistant state changes"""
    logging.error(f"WebSocket connection established")
    
    # WebSocket client for HA connection
    ha_ws_client = None
    
    def close_ha_websocket():
        """Helper to safely close HA WebSocket connection"""
        nonlocal ha_ws_client
        if ha_ws_client:
            try:
                ha_ws_client.close()
            except:
                pass
            ha_ws_client = None

    def forward_ha_websocket():
        """Forward messages from Home Assistant WebSocket to frontend"""
        nonlocal ha_ws_client
        
        try:
            import websocket
            
            # Determine WebSocket URL
            if SUPERVISOR_TOKEN:
                ha_ws_url = 'ws://supervisor/core/websocket'
                auth_headers = [f'Authorization: Bearer {SUPERVISOR_TOKEN}']
            else:
                ha_ws_url = HA_URL.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/') + '/websocket'
                auth_headers = [f'Authorization: Bearer {HA_TOKEN}']
            
            logging.error(f"HA WebSocket connecting to: {ha_ws_url}")
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    
                    # Only forward state_changed events for entities we care about
                    if (data.get('type') == 'event' and 
                        data.get('event', {}).get('event_type') == 'state_changed'):
                        
                        entity_id = data.get('event', {}).get('data', {}).get('entity_id')
                        
                        # Check if this is an entity the frontend is interested in
                        global selected_entity_ids
                        if entity_id and (not selected_entity_ids or entity_id in selected_entity_ids):
                            # Additional filter: only forward mmWave-related entities
                            if is_mmwave_entity(entity_id):
                                sock.send(json.dumps(data))
                                logging.error(f"Forwarded state change for: {entity_id}")
                        
                except json.JSONDecodeError:
                    logging.error(f"Invalid JSON from HA WebSocket: {message}")
                except Exception as e:
                    logging.error(f"Error processing HA WebSocket message: {e}")
            
            def on_error(ws, error):
                logging.error(f"HA WebSocket error: {error}")
                sock.send(json.dumps({'type': 'error', 'message': str(error)}))
            
            def on_close(ws, close_status_code, close_msg):
                logging.error("HA WebSocket connection closed")
                sock.send(json.dumps({'type': 'connection_closed', 'message': 'Home Assistant WebSocket closed'}))
            
            def on_open(ws):
                logging.error("HA WebSocket connection opened")
                # Send auth message
                auth_msg = {
                    "type": "auth",
                    "access_token": SUPERVISOR_TOKEN if SUPERVISOR_TOKEN else HA_TOKEN
                }
                ws.send(json.dumps(auth_msg))
                
                # Subscribe to state changes after successful auth
                def send_subscribe():
                    time.sleep(1)  # Wait for auth to complete
                    subscribe_msg = {
                        "id": 1,
                        "type": "subscribe_events",
                        "event_type": "state_changed"
                    }
                    try:
                        ws.send(json.dumps(subscribe_msg))
                        logging.error("Subscribed to state_changed events")
                    except Exception as e:
                        logging.error(f"Failed to subscribe to events: {e}")
                
                # Send subscribe in a separate thread to avoid blocking
                threading.Thread(target=send_subscribe, daemon=True).start()
                
                sock.send(json.dumps({'type': 'connected', 'message': 'Connected to Home Assistant'}))
            
            # Create WebSocket client
            ha_ws_client = websocket.WebSocketApp(
                ha_ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                header=auth_headers
            )
            
            # Run WebSocket client
            ha_ws_client.run_forever()
            
        except ImportError:
            logging.error("websocket-client not available, WebSocket forwarding disabled")
            sock.send(json.dumps({'type': 'error', 'message': 'WebSocket forwarding not available'}))
        except Exception as e:
            logging.error(f"HA WebSocket connection failed: {e}")
            sock.send(json.dumps({'type': 'error', 'message': f'WebSocket connection failed: {str(e)}'}))
    
    try:
        # Start HA WebSocket forwarding in background thread
        ha_thread = threading.Thread(target=forward_ha_websocket, daemon=True)
        ha_thread.start()
        
        # Handle messages from frontend
        while True:
            try:
                message = sock.receive()
                if message:
                    data = json.loads(message)
                    if data.get('type') == 'ping':
                        sock.send(json.dumps({'type': 'pong'}))
                    elif data.get('type') == 'set_selected_entities':
                        # Update selected entities for filtering
                        entity_ids = data.get('entity_ids', [])
                        global selected_entity_ids
                        selected_entity_ids = set(entity_ids)
                        sock.send(json.dumps({'type': 'entities_updated', 'count': len(selected_entity_ids)}))
                        logging.error(f"Updated selected entities: {len(selected_entity_ids)} entities")
                    
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON from frontend: {message}")
            except Exception as e:
                logging.error(f"Error handling frontend message: {e}")
                break
                
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        close_ha_websocket()
        logging.error("WebSocket connection closed")

if __name__ == '__main__':
    check_connectivity()
    app.run(host='0.0.0.0', port=5000, debug=True)
