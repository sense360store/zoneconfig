#!/usr/bin/env python3
"""
Test Orphaned Manifest Cleanup
==============================

This script specifically tests the cleanup of orphaned firmware-*.json files
to ensure the automation properly removes stale manifests.

Usage:
  python3 test-orphaned-cleanup.py
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def log(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_orphaned_manifests():
    """Create fake orphaned manifest files."""
    orphaned_files = [
        'firmware-99.json',
        'firmware-old.json',
        'firmware-deleted.json',
        'firmware-orphaned.json'
    ]
    
    log("Creating orphaned manifest files...")
    for filename in orphaned_files:
        with open(filename, 'w') as f:
            json.dump({
                "name": "Orphaned Firmware",
                "version": "1.0.0",
                "builds": []
            }, f, indent=2)
        log(f"  Created: {filename}")
    
    return orphaned_files

def count_manifests():
    """Count existing manifest files."""
    manifest_files = list(Path('.').glob('firmware-*.json'))
    return len(manifest_files), [str(f) for f in manifest_files]

def run_automation():
    """Run the automation script."""
    result = subprocess.run(['python3', 'deploy-automation.py'], 
                          capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def test_orphaned_cleanup():
    """Test the orphaned manifest cleanup functionality."""
    log("=" * 60)
    log("TESTING ORPHANED MANIFEST CLEANUP")
    log("=" * 60)
    
    # Step 1: Check initial state
    initial_count, initial_files = count_manifests()
    log(f"Initial state: {initial_count} manifest files")
    for f in initial_files:
        log(f"  - {f}")
    
    # Step 2: Create orphaned manifests
    orphaned_files = create_orphaned_manifests()
    
    # Step 3: Check state after creating orphans
    after_orphans_count, after_orphans_files = count_manifests()
    log(f"After creating orphans: {after_orphans_count} manifest files")
    for f in after_orphans_files:
        log(f"  - {f}")
    
    # Step 4: Run automation
    log("Running automation to clean up orphaned manifests...")
    success, stdout, stderr = run_automation()
    
    if not success:
        log(f"❌ Automation failed: {stderr}")
        return False
    
    # Step 5: Check state after automation
    final_count, final_files = count_manifests()
    log(f"After automation: {final_count} manifest files")
    for f in final_files:
        log(f"  - {f}")
    
    # Step 6: Verify cleanup worked
    firmware_count = len(list(Path('firmware').rglob('*.bin')))
    log(f"Firmware files: {firmware_count}")
    
    if final_count == firmware_count:
        log("✅ SUCCESS: Orphaned manifests cleaned up properly")
        log(f"✅ Perfect synchronization: {firmware_count} firmware = {final_count} manifests")
        return True
    else:
        log("❌ FAILURE: Orphaned manifests not cleaned up properly")
        log(f"❌ Expected {firmware_count} manifests, got {final_count}")
        return False

def main():
    """Run the orphaned cleanup test."""
    try:
        success = test_orphaned_cleanup()
        if success:
            print("\n🎉 ORPHANED CLEANUP TEST PASSED!")
            return 0
        else:
            print("\n❌ ORPHANED CLEANUP TEST FAILED!")
            return 1
    except Exception as e:
        print(f"\n💥 TEST CRASHED: {e}")
        return 1

if __name__ == '__main__':
    exit(main())