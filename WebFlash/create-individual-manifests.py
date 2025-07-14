#!/usr/bin/env python3
"""
Create individual manifest files for each firmware build.
This script generates static manifest files that ESP Web Tools can use.
"""

import json
import os
from pathlib import Path
from urllib.parse import urljoin

def create_individual_manifests():
    """Create individual manifest files for each firmware build."""
    
    # Read the main manifest
    with open('manifest.json', 'r') as f:
        main_manifest = json.load(f)
    
    # Use relative URLs for GitHub Pages deployment
    # This ensures the URLs work in any deployment environment
    base_url = ""
    
    # Create individual manifests for each build
    for index, build in enumerate(main_manifest['builds']):
        # Create individual manifest
        individual_manifest = {
            "name": f"{main_manifest['name']} - {build['device_type']}",
            "version": build['version'],
            "home_assistant_domain": main_manifest['home_assistant_domain'],
            "new_install_skip_erase": main_manifest['new_install_skip_erase'],
            "builds": [{
                "chipFamily": build['chipFamily'],
                "parts": [{
                    "path": build['parts'][0]['path'],
                    "offset": build['parts'][0]['offset']
                }],
                "improv": True
            }]
        }
        
        # Write individual manifest file
        manifest_filename = f'firmware-{index}.json'
        with open(manifest_filename, 'w') as f:
            json.dump(individual_manifest, f, indent=2)
        
        print(f"Created {manifest_filename} for {build['device_type']} v{build['version']}")
        print(f"  Firmware URL: {individual_manifest['builds'][0]['parts'][0]['path']}")
        print(f"  File exists: {os.path.exists(build['parts'][0]['path'])}")
        print()

if __name__ == '__main__':
    create_individual_manifests()