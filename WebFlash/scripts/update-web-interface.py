#!/usr/bin/env python3
"""
Update the web interface to show multiple firmware options dynamically.
This script modifies index.html to display all available firmware options.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def get_firmware_timestamp(build):
    """Get formatted timestamp for firmware build."""
    if 'build_date' in build:
        try:
            dt = datetime.fromisoformat(build['build_date'])
            return dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            pass
    return 'Unknown'

def generate_firmware_options_html(manifest_file="manifest.json"):
    """Generate HTML for firmware options based on manifest.json."""
    
    if not os.path.exists(manifest_file):
        return '<p>No firmware manifest found. Please run update-manifest.py first.</p>'
    
    with open(manifest_file, 'r') as f:
        manifest = json.load(f)
    
    if not manifest.get('builds'):
        return '<p>No firmware builds available.</p>'
    
    html = []
    
    for index, build in enumerate(manifest['builds']):
        device_type = build.get('device_type', 'Unknown')
        version = build.get('version', '1.0.0')
        channel = build.get('channel', 'stable')
        chip_family = build.get('chipFamily', 'ESP32')
        build_date = get_firmware_timestamp(build)
        file_size = build.get('file_size', 0)
        
        # Convert file size to human readable format
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        # Channel styling
        channel_class = 'stable' if channel == 'stable' else 'beta'
        
        html.append(f'''
                <div class="build-item" data-firmware-index="{index}" onclick="selectFirmware({index})">
                    <div class="build-header">
                        <h3>{device_type} v{version}</h3>
                        <span class="channel-badge {channel_class}">{channel}</span>
                    </div>
                    <div class="build-details">
                        <span class="chip-family">{chip_family}</span>
                        <span class="build-date">Built: {build_date}</span>
                        <span class="file-size">{size_str}</span>
                    </div>
                </div>''')
    
    return ''.join(html)

def update_index_html(html_file="index.html", manifest_file="manifest.json"):
    """Update index.html with generated firmware options."""
    
    if not os.path.exists(html_file):
        print(f"HTML file {html_file} not found")
        return False
    
    # Generate firmware options HTML
    firmware_html = generate_firmware_options_html(manifest_file)
    
    # Read current HTML
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Find the firmware details section and replace it
    start_marker = '<div id="firmware-details">'
    end_marker = '</div>'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Could not find firmware-details section in HTML")
        return False
    
    # Find the complete firmware-details div by counting opening and closing divs
    start_idx += len(start_marker)
    div_count = 1
    search_pos = start_idx
    
    while div_count > 0 and search_pos < len(content):
        next_open = content.find('<div', search_pos)
        next_close = content.find('</div>', search_pos)
        
        if next_close == -1:
            print("Could not find closing div for firmware-details")
            return False
        
        if next_open != -1 and next_open < next_close:
            div_count += 1
            search_pos = next_open + 4
        else:
            div_count -= 1
            search_pos = next_close + 6
    
    end_idx = search_pos - 6  # Back up to the start of the last </div>
    
    # Replace the content
    new_content = (
        content[:start_idx] + 
        '\n                ' + firmware_html + '\n            ' +
        content[end_idx:]
    )
    
    # Write updated HTML
    with open(html_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated {html_file} with firmware options")
    return True

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Update web interface with firmware options')
    parser.add_argument('--html-file', default='index.html', help='HTML file to update')
    parser.add_argument('--manifest-file', default='manifest.json', help='Manifest file to read')
    
    args = parser.parse_args()
    
    if update_index_html(args.html_file, args.manifest_file):
        print("Web interface updated successfully")
    else:
        print("Failed to update web interface")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())