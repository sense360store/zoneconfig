#!/usr/bin/env python3
"""
Firmware Binary Management Script
================================

Automatically scans firmware/ directory and updates manifest.json for ESP Web Tools.
Extracts metadata from filename/directory structure following naming convention:
  Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin

Usage:
  python3 scripts/update-manifest.py
  python3 scripts/update-manifest.py --firmware-dir custom/firmware/path
"""

import json
import os
import argparse
from pathlib import Path
from datetime import datetime
import re

class FirmwareBinaryManager:
    def __init__(self, firmware_dir: str = "firmware", manifest_path: str = "manifest.json"):
        self.firmware_dir = Path(firmware_dir)
        self.manifest_path = Path(manifest_path)
        self.base_url = "http://localhost:5000/"
        
    def extract_metadata_from_filename(self, filename: str) -> dict:
        """Extract metadata from firmware filename following naming convention."""
        # Pattern: Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin
        pattern = r'Sense360-([^-]+)-([^-]+)-v([^-]+)-([^.]+)\.bin'
        match = re.match(pattern, filename)
        
        if match:
            device_type, chip_family, version, channel = match.groups()
            return {
                'device_type': device_type,
                'chip_family': chip_family,
                'version': version,
                'channel': channel
            }
        return None
    
    def extract_metadata_from_path(self, file_path: Path) -> dict:
        """Extract metadata from directory structure: firmware/[DeviceType]/[ChipFamily]/[Channel]/"""
        parts = file_path.parts
        if len(parts) >= 4:
            # Extract from directory structure
            device_type = parts[-4]  # firmware/DeviceType/ChipFamily/Channel/file.bin
            chip_family = parts[-3]
            channel = parts[-2]
            
            # Extract version from filename
            filename_metadata = self.extract_metadata_from_filename(file_path.name)
            version = filename_metadata.get('version', '1.0.0') if filename_metadata else '1.0.0'
            
            return {
                'device_type': device_type,
                'chip_family': chip_family,
                'version': version,
                'channel': channel
            }
        return None
    
    def get_chip_family_mapping(self, chip_family: str) -> str:
        """Map chip family to ESP Web Tools format."""
        mapping = {
            'ESP32': 'ESP32',
            'ESP32S2': 'ESP32-S2',
            'ESP32S3': 'ESP32-S3',
            'ESP32C3': 'ESP32-C3',
            'ESP32C6': 'ESP32-C6',
            'ESP32H2': 'ESP32-H2'
        }
        return mapping.get(chip_family, chip_family)
    
    def scan_firmware_directory(self) -> list:
        """Scan firmware directory and return list of firmware files with metadata."""
        firmware_files = []
        
        if not self.firmware_dir.exists():
            print(f"Firmware directory {self.firmware_dir} does not exist")
            return firmware_files
            
        for bin_file in self.firmware_dir.rglob("*.bin"):
            # Extract metadata from directory structure
            metadata = self.extract_metadata_from_path(bin_file)
            
            if metadata:
                firmware_files.append({
                    'path': str(bin_file),
                    'relative_path': str(bin_file.relative_to(Path('.'))),
                    'metadata': metadata,
                    'size': bin_file.stat().st_size,
                    'modified': datetime.fromtimestamp(bin_file.stat().st_mtime).isoformat()
                })
                print(f"Found: {bin_file.name} - {metadata['device_type']} v{metadata['version']} ({metadata['chip_family']})")
            else:
                print(f"Warning: Could not extract metadata from {bin_file}")
                
        return firmware_files
    
    def generate_manifest_builds(self, firmware_files: list) -> list:
        """Generate manifest builds array from firmware files."""
        builds = []
        
        for firmware in firmware_files:
            metadata = firmware['metadata']
            
            build = {
                "device_type": metadata['device_type'],
                "version": metadata['version'],
                "channel": metadata['channel'],
                "chipFamily": self.get_chip_family_mapping(metadata['chip_family']),
                "parts": [{
                    "path": firmware['relative_path'],
                    "offset": 0
                }],
                "build_date": firmware['modified'],
                "file_size": firmware['size']
            }
            
            builds.append(build)
            
        # Sort by device type, then version
        builds.sort(key=lambda x: (x['device_type'], x['version']))
        return builds
    
    def update_manifest(self) -> bool:
        """Update manifest.json with all available firmware."""
        try:
            # Scan firmware directory
            firmware_files = self.scan_firmware_directory()
            
            if not firmware_files:
                print("No firmware files found")
                return False
            
            # Generate builds array
            builds = self.generate_manifest_builds(firmware_files)
            
            # Create manifest structure
            manifest = {
                "name": "Sense360 ESP32 Firmware",
                "version": "1.0.0",
                "home_assistant_domain": "esphome",
                "new_install_skip_erase": False,
                "builds": builds
            }
            
            # Write manifest.json
            with open(self.manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"Updated {self.manifest_path} with {len(builds)} firmware builds")
            return True
            
        except Exception as e:
            print(f"Error updating manifest: {e}")
            return False
    
    def validate_manifest(self) -> bool:
        """Validate generated manifest.json format."""
        try:
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            required_fields = ['name', 'version', 'builds']
            for field in required_fields:
                if field not in manifest:
                    print(f"Missing required field: {field}")
                    return False
            
            # Validate builds
            for build in manifest['builds']:
                if 'chipFamily' not in build or 'parts' not in build:
                    print(f"Invalid build structure: {build}")
                    return False
                    
                for part in build['parts']:
                    if 'path' not in part or 'offset' not in part:
                        print(f"Invalid part structure: {part}")
                        return False
            
            print("Manifest validation passed")
            return True
            
        except Exception as e:
            print(f"Manifest validation failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Update firmware manifest from directory scan')
    parser.add_argument('--firmware-dir', default='firmware', help='Firmware directory to scan')
    parser.add_argument('--manifest-path', default='manifest.json', help='Output manifest file path')
    parser.add_argument('--validate', action='store_true', help='Validate manifest after generation')
    
    args = parser.parse_args()
    
    manager = FirmwareBinaryManager(args.firmware_dir, args.manifest_path)
    
    # Update manifest
    if manager.update_manifest():
        print("Manifest updated successfully")
        
        # Validate if requested
        if args.validate:
            manager.validate_manifest()
    else:
        print("Failed to update manifest")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())