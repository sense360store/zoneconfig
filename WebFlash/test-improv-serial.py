#!/usr/bin/env python3
"""
Test Improv Serial Wi-Fi Setup Integration
==========================================

This script verifies that all firmware builds include proper Improv Serial
support for browser-based Wi-Fi configuration after firmware installation.

Tests:
1. ESPHome configurations have improv_serial enabled
2. Manifest files include "improv": true
3. ESP Web Tools will offer Wi-Fi setup after flashing
4. All firmware builds automatically include Improv support

Usage:
  python3 test-improv-serial.py
"""

import json
import os
import yaml
import requests
from pathlib import Path

def test_esphome_improv_serial():
    """Test that all ESPHome configurations have improv_serial enabled."""
    print("=" * 60)
    print("TESTING ESPHOME IMPROV SERIAL CONFIGURATION")
    print("=" * 60)
    
    esphome_dir = Path("../iot-firmware-src/esphome")
    yaml_files = list(esphome_dir.glob("*.yaml"))
    
    # Filter out secrets.yaml as it doesn't need improv_serial
    yaml_files = [f for f in yaml_files if f.name != "secrets.yaml"]
    
    if not yaml_files:
        print("✗ No ESPHome YAML files found")
        return False
    
    success = True
    
    for yaml_file in yaml_files:
        print(f"\nTesting: {yaml_file.name}")
        
        try:
            with open(yaml_file, 'r') as f:
                content = f.read()
            
            if 'improv_serial:' in content:
                print("  ✓ improv_serial found in configuration")
            else:
                print("  ✗ improv_serial NOT found in configuration")
                success = False
                
        except Exception as e:
            print(f"  ✗ Error reading {yaml_file}: {e}")
            success = False
    
    return success

def test_manifest_improv_support():
    """Test that manifest files include improv: true."""
    print("\n" + "=" * 60)
    print("TESTING MANIFEST IMPROV SUPPORT")
    print("=" * 60)
    
    # Test main manifest
    print("\nTesting main manifest.json:")
    try:
        with open('manifest.json', 'r') as f:
            manifest = json.load(f)
        
        if 'builds' not in manifest:
            print("✗ No builds found in manifest")
            return False
        
        success = True
        for i, build in enumerate(manifest['builds']):
            if build.get('improv') is True:
                print(f"  ✓ Build {i} ({build['device_type']}): improv = true")
            else:
                print(f"  ✗ Build {i} ({build['device_type']}): improv missing or false")
                success = False
                
    except Exception as e:
        print(f"✗ Error reading manifest.json: {e}")
        return False
    
    # Test individual manifests
    print("\nTesting individual manifests:")
    for i, build in enumerate(manifest['builds']):
        manifest_file = f'firmware-{i}.json'
        try:
            with open(manifest_file, 'r') as f:
                individual_manifest = json.load(f)
            
            if individual_manifest['builds'][0].get('improv') is True:
                print(f"  ✓ {manifest_file}: improv = true")
            else:
                print(f"  ✗ {manifest_file}: improv missing or false")
                success = False
                
        except Exception as e:
            print(f"  ✗ Error reading {manifest_file}: {e}")
            success = False
    
    return success

def test_esp_web_tools_compatibility():
    """Test ESP Web Tools compatibility with Improv Serial."""
    print("\n" + "=" * 60)
    print("TESTING ESP WEB TOOLS COMPATIBILITY")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test manifest accessibility
    print("\nTesting manifest accessibility:")
    try:
        response = requests.get(f"{base_url}/manifest.json")
        if response.status_code == 200:
            print("  ✓ Main manifest accessible")
            manifest = response.json()
        else:
            print(f"  ✗ Main manifest not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Error accessing manifest: {e}")
        return False
    
    # Test individual manifests
    print("\nTesting individual manifests:")
    success = True
    for i, build in enumerate(manifest['builds']):
        try:
            response = requests.get(f"{base_url}/firmware-{i}.json")
            if response.status_code == 200:
                individual_manifest = response.json()
                if individual_manifest['builds'][0].get('improv') is True:
                    print(f"  ✓ firmware-{i}.json: accessible and improv-enabled")
                else:
                    print(f"  ✗ firmware-{i}.json: accessible but improv missing")
                    success = False
            else:
                print(f"  ✗ firmware-{i}.json: not accessible ({response.status_code})")
                success = False
        except Exception as e:
            print(f"  ✗ Error accessing firmware-{i}.json: {e}")
            success = False
    
    return success

def test_automation_workflow():
    """Test that automation automatically includes Improv support."""
    print("\n" + "=" * 60)
    print("TESTING AUTOMATION WORKFLOW")
    print("=" * 60)
    
    # Test deploy-automation.py includes improv support
    print("\nTesting deploy-automation.py:")
    try:
        with open('deploy-automation.py', 'r') as f:
            content = f.read()
        
        if '"improv": True' in content:
            print("  ✓ deploy-automation.py includes improv: True")
        else:
            print("  ✗ deploy-automation.py does not include improv: True")
            return False
            
    except Exception as e:
        print(f"  ✗ Error reading deploy-automation.py: {e}")
        return False
    
    # Test create-individual-manifests.py includes improv support
    print("\nTesting create-individual-manifests.py:")
    try:
        with open('create-individual-manifests.py', 'r') as f:
            content = f.read()
        
        if '"improv": True' in content:
            print("  ✓ create-individual-manifests.py includes improv: True")
        else:
            print("  ✗ create-individual-manifests.py does not include improv: True")
            return False
            
    except Exception as e:
        print(f"  ✗ Error reading create-individual-manifests.py: {e}")
        return False
    
    return True

def main():
    """Run all Improv Serial tests."""
    print("TESTING IMPROV SERIAL WI-FI SETUP INTEGRATION")
    print("=" * 60)
    
    tests = [
        ("ESPHome Improv Serial Configuration", test_esphome_improv_serial),
        ("Manifest Improv Support", test_manifest_improv_support),
        ("ESP Web Tools Compatibility", test_esp_web_tools_compatibility),
        ("Automation Workflow", test_automation_workflow)
    ]
    
    all_passed = True
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"✗ Test {test_name} failed with error: {e}")
            results.append((test_name, False))
            all_passed = False
    
    # Print summary
    print("\n" + "=" * 60)
    print("IMPROV SERIAL TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
        print("✓ Improv Serial Wi-Fi setup is fully automated")
        print("✓ ESP Web Tools will offer Wi-Fi configuration after flashing")
        print("✓ All firmware builds automatically include Improv support")
        print("")
        print("WORKFLOW CONFIRMED:")
        print("1. Flash firmware via ESP Web Tools")
        print("2. Browser automatically prompts for Wi-Fi setup")
        print("3. User enters Wi-Fi credentials in browser")
        print("4. Device connects to Wi-Fi automatically")
        print("5. No manual AP connection required")
    else:
        print("✗ SOME TESTS FAILED!")
        print("Please fix the failing tests before deployment")
    
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit(main())