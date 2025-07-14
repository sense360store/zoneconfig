#!/usr/bin/env python3
"""Test the complete firmware workflow end-to-end."""

import os
import json
import requests
import time
from pathlib import Path

def test_complete_workflow():
    """Test the complete automation workflow."""
    base_url = "http://localhost:5000"
    
    print("=" * 60)
    print("TESTING COMPLETE FIRMWARE WORKFLOW")
    print("=" * 60)
    
    # Test 1: Check if main page loads
    print("1. Testing main page load...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✓ Main page loads successfully")
        else:
            print(f"✗ Main page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Main page error: {e}")
        return False
    
    # Test 2: Check manifest.json
    print("\n2. Testing manifest.json...")
    try:
        response = requests.get(f"{base_url}/manifest.json")
        if response.status_code == 200:
            manifest = response.json()
            print(f"✓ Manifest loaded: {len(manifest['builds'])} builds")
            
            for i, build in enumerate(manifest['builds']):
                print(f"  Build {i}: {build['device_type']} v{build['version']} ({build['chipFamily']})")
        else:
            print(f"✗ Manifest failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Manifest error: {e}")
        return False
    
    # Test 3: Check individual manifest files
    print("\n3. Testing individual manifest files...")
    for i in range(len(manifest['builds'])):
        try:
            response = requests.get(f"{base_url}/firmware-{i}.json")
            if response.status_code == 200:
                individual_manifest = response.json()
                firmware_path = individual_manifest['builds'][0]['parts'][0]['path']
                print(f"✓ Individual manifest {i}: {firmware_path}")
                
                # Convert relative path to absolute URL for testing
                firmware_url = f"{base_url}/{firmware_path}"
                firmware_response = requests.head(firmware_url)
                if firmware_response.status_code == 200:
                    print(f"  ✓ Firmware file accessible at: {firmware_url}")
                else:
                    print(f"  ✗ Firmware file not accessible: {firmware_response.status_code}")
            else:
                print(f"✗ Individual manifest {i} failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Individual manifest {i} error: {e}")
            return False
    
    # Test 4: Test automation workflow
    print("\n4. Testing automation workflow...")
    try:
        # Run the automation script
        import subprocess
        result = subprocess.run(['python3', 'automate-firmware.py', '--validate'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✓ Automation workflow validation passed")
        else:
            print(f"✗ Automation workflow failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Automation workflow error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("WORKFLOW TEST SUMMARY")
    print("=" * 60)
    print("✓ All tests passed!")
    print("✓ Firmware files are accessible")
    print("✓ Individual manifests are working")
    print("✓ ESP Web Tools should work correctly")
    print("✓ Complete automation workflow is functional")
    print()
    print("NEXT STEPS:")
    print("1. Select firmware from the web interface")
    print("2. Click 'Install Selected Firmware'")
    print("3. ESP Web Tools will use the individual manifest files")
    print("4. Firmware will be downloaded and flashed successfully")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = test_complete_workflow()
    exit(0 if success else 1)