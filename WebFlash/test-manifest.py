#!/usr/bin/env python3
"""Test the individual manifest files"""

import json
import requests
import os

def test_manifest_files():
    """Test that the individual manifest files are accessible and valid"""
    
    base_url = "http://localhost:5000/WebFlash"
    
    # Test each individual manifest file
    for i in range(5):
        manifest_filename = f'firmware-{i}.json'
        manifest_url = f'{base_url}/{manifest_filename}'
        
        try:
            response = requests.get(manifest_url)
            print(f"Testing {manifest_filename}:")
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                manifest = response.json()
                print(f"  Name: {manifest['name']}")
                print(f"  Version: {manifest['version']}")
                print(f"  Chip Family: {manifest['builds'][0]['chipFamily']}")
                print(f"  Firmware URL: {manifest['builds'][0]['parts'][0]['path']}")
                
                # Test if firmware file exists
                firmware_path = manifest['builds'][0]['parts'][0]['path']
                firmware_response = requests.head(firmware_path)
                print(f"  Firmware accessible: {firmware_response.status_code == 200}")
            else:
                print(f"  Error: {response.text}")
                
        except Exception as e:
            print(f"  Error: {e}")
            
        print()

if __name__ == '__main__':
    test_manifest_files()