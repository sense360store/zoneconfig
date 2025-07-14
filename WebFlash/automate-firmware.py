#!/usr/bin/env python3
"""
Complete Firmware Automation Script
===================================

This script provides 100% automation for the firmware management system.
Simply add/remove .bin files in the firmware/ directory and run this script.

Features:
- Scans firmware/ directory for .bin files
- Extracts metadata from directory structure and filenames
- Updates manifest.json with all available firmware
- Creates individual manifest files for ESP Web Tools
- Updates web interface with firmware options
- Validates all generated files

Usage:
  python3 automate-firmware.py              # Full automation
  python3 automate-firmware.py --watch      # Watch for changes (future)
  python3 automate-firmware.py --validate   # Only validate existing files
"""

import json
import os
import sys
from pathlib import Path
import subprocess
import argparse
from datetime import datetime

class FirmwareAutomation:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.firmware_dir = self.base_dir / "firmware"
        self.manifest_path = self.base_dir / "manifest.json"
        self.index_path = self.base_dir / "index.html"
        self.scripts_dir = self.base_dir / "scripts"
        
    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def check_dependencies(self) -> bool:
        """Check if all required scripts and files exist."""
        required_files = [
            self.scripts_dir / "update-manifest.py",
            self.scripts_dir / "update-web-interface.py",
            self.index_path
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                self.log(f"ERROR: Required file not found: {file_path}")
                return False
        
        return True
    
    def scan_firmware_directory(self) -> dict:
        """Scan firmware directory and return summary."""
        if not self.firmware_dir.exists():
            self.log(f"ERROR: Firmware directory {self.firmware_dir} does not exist")
            return {'found': 0, 'files': []}
        
        bin_files = list(self.firmware_dir.rglob("*.bin"))
        
        summary = {
            'found': len(bin_files),
            'files': [],
            'devices': set(),
            'versions': set(),
            'chips': set()
        }
        
        for bin_file in bin_files:
            file_info = {
                'path': str(bin_file),
                'name': bin_file.name,
                'size': bin_file.stat().st_size,
                'modified': datetime.fromtimestamp(bin_file.stat().st_mtime)
            }
            summary['files'].append(file_info)
            
            # Extract metadata for summary
            parts = bin_file.parts
            if len(parts) >= 4:
                device_type = parts[-4]
                chip_family = parts[-3]
                channel = parts[-2]
                summary['devices'].add(device_type)
                summary['chips'].add(chip_family)
        
        return summary
    
    def update_manifest(self) -> bool:
        """Update manifest.json from firmware directory."""
        self.log("Updating manifest.json...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.scripts_dir / "update-manifest.py"),
                "--validate"
            ], capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                self.log("✓ Manifest updated successfully")
                return True
            else:
                self.log(f"ERROR: Manifest update failed: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to run update-manifest.py: {e}")
            return False
    
    def create_individual_manifests(self) -> bool:
        """Create individual manifest files for each firmware."""
        self.log("Creating individual manifest files...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                "create-individual-manifests.py"
            ], capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                self.log("✓ Individual manifests created successfully")
                return True
            else:
                self.log(f"ERROR: Individual manifest creation failed: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to run create-individual-manifests.py: {e}")
            return False
    
    def update_web_interface(self) -> bool:
        """Update web interface with firmware options."""
        self.log("Updating web interface...")
        
        try:
            result = subprocess.run([
                sys.executable, 
                str(self.scripts_dir / "update-web-interface.py")
            ], capture_output=True, text=True, cwd=self.base_dir)
            
            if result.returncode == 0:
                self.log("✓ Web interface updated successfully")
                return True
            else:
                self.log(f"ERROR: Web interface update failed: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"ERROR: Failed to run update-web-interface.py: {e}")
            return False
    
    def validate_generated_files(self) -> bool:
        """Validate all generated files."""
        self.log("Validating generated files...")
        
        # Check manifest.json
        if not self.manifest_path.exists():
            self.log("ERROR: manifest.json not found")
            return False
        
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            if not manifest.get('builds'):
                self.log("ERROR: No builds found in manifest.json")
                return False
            
            # Check individual manifests
            for i, build in enumerate(manifest['builds']):
                individual_manifest = self.base_dir / f"firmware-{i}.json"
                if not individual_manifest.exists():
                    self.log(f"ERROR: Individual manifest {individual_manifest} not found")
                    return False
                
                # Check if firmware file exists
                firmware_path = self.base_dir / build['parts'][0]['path']
                if not firmware_path.exists():
                    self.log(f"ERROR: Firmware file not found: {firmware_path}")
                    return False
            
            self.log("✓ All generated files validated successfully")
            return True
            
        except Exception as e:
            self.log(f"ERROR: Validation failed: {e}")
            return False
    
    def print_summary(self, firmware_summary: dict):
        """Print automation summary."""
        self.log("=" * 60)
        self.log("FIRMWARE AUTOMATION SUMMARY")
        self.log("=" * 60)
        self.log(f"Firmware files found: {firmware_summary['found']}")
        self.log(f"Device types: {', '.join(sorted(firmware_summary['devices']))}")
        self.log(f"Chip families: {', '.join(sorted(firmware_summary['chips']))}")
        self.log("")
        
        if firmware_summary['files']:
            self.log("FIRMWARE FILES:")
            for file_info in firmware_summary['files']:
                size_mb = file_info['size'] / (1024 * 1024)
                self.log(f"  {file_info['name']} ({size_mb:.1f} MB)")
        
        self.log("")
        self.log("AUTOMATION COMPLETE")
        self.log("Web interface updated with all firmware options")
        self.log("Users can now select and install firmware via ESP Web Tools")
        self.log("=" * 60)
    
    def run_full_automation(self) -> bool:
        """Run complete firmware automation workflow."""
        self.log("Starting firmware automation...")
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("ERROR: Missing dependencies. Please ensure all scripts are in place.")
            return False
        
        # Scan firmware directory
        firmware_summary = self.scan_firmware_directory()
        if firmware_summary['found'] == 0:
            self.log("No firmware files found. Please add .bin files to firmware/ directory.")
            return False
        
        # Run automation steps
        steps = [
            ("Update manifest", self.update_manifest),
            ("Create individual manifests", self.create_individual_manifests),
            ("Update web interface", self.update_web_interface),
            ("Validate generated files", self.validate_generated_files)
        ]
        
        for step_name, step_func in steps:
            self.log(f"Running: {step_name}")
            if not step_func():
                self.log(f"ERROR: {step_name} failed")
                return False
        
        # Print summary
        self.print_summary(firmware_summary)
        return True

def main():
    parser = argparse.ArgumentParser(description='Complete firmware automation')
    parser.add_argument('--validate', action='store_true', help='Only validate existing files')
    parser.add_argument('--base-dir', default='.', help='Base directory for automation')
    
    args = parser.parse_args()
    
    automation = FirmwareAutomation(args.base_dir)
    
    if args.validate:
        if automation.validate_generated_files():
            print("Validation passed")
            return 0
        else:
            print("Validation failed")
            return 1
    else:
        if automation.run_full_automation():
            print("Automation completed successfully")
            return 0
        else:
            print("Automation failed")
            return 1

if __name__ == '__main__':
    exit(main())