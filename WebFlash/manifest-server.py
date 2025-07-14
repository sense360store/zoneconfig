#!/usr/bin/env python3
"""
Simple HTTP server for serving firmware manifests dynamically.
This handles the dynamic manifest generation for ESP Web Tools.
"""

import http.server
import socketserver
import urllib.parse
import json
import os
from pathlib import Path

class ManifestRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # Handle dynamic manifest requests
        if parsed_path.path == '/selected-firmware.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Parse query parameters to get selected firmware index
            query_params = urllib.parse.parse_qs(parsed_path.query)
            selected_index = int(query_params.get('index', ['0'])[0])
            
            try:
                with open('manifest.json', 'r') as f:
                    main_manifest = json.load(f)
                
                # Get the selected build by index
                if main_manifest.get('builds') and selected_index < len(main_manifest['builds']):
                    selected_build = main_manifest['builds'][selected_index]
                    
                    # Build absolute URLs for firmware parts
                    base_url = f"http://{self.headers.get('Host', 'localhost:5000')}"
                    
                    selected_manifest = {
                        "name": f"{main_manifest['name']} - {selected_build['device_type']}",
                        "version": selected_build['version'],
                        "home_assistant_domain": main_manifest['home_assistant_domain'],
                        "new_install_skip_erase": main_manifest['new_install_skip_erase'],
                        "builds": [{
                            "chipFamily": selected_build['chipFamily'],
                            "parts": [{
                                "path": f"{base_url}/{selected_build['parts'][0]['path']}",
                                "offset": selected_build['parts'][0]['offset']
                            }]
                        }]
                    }
                    
                    print(f"Serving selected firmware (index {selected_index}): {selected_build['device_type']} v{selected_build['version']}")
                    print(f"Firmware URL: {selected_manifest['builds'][0]['parts'][0]['path']}")
                else:
                    selected_manifest = {
                        "name": "Invalid Firmware Selection",
                        "version": "1.0.0",
                        "builds": []
                    }
            except Exception as e:
                print(f"Error reading manifest: {e}")
                selected_manifest = {
                    "name": "Error Loading Firmware",
                    "version": "1.0.0",
                    "builds": []
                }
            
            self.wfile.write(json.dumps(selected_manifest).encode())
            return
        
        # Handle CORS preflight
        if self.command == 'OPTIONS':
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            return
            
        # Add CORS headers to all responses
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
        
        # Default file serving
        super().do_GET()

def main():
    PORT = 5000
    Handler = ManifestRequestHandler
    
    # Change to WebFlash directory
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving firmware installer at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()

if __name__ == "__main__":
    main()