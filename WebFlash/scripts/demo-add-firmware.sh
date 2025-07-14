#!/bin/bash
# Demo script showing one-step firmware addition process

echo "=== Sense360 One-Step Firmware Addition Demo ==="
echo

# Step 1: Simulate adding a new firmware binary
echo "Step 1: Adding new firmware binary..."
mkdir -p firmware/TempSensor/ESP32C3/stable/
echo "EXAMPLE_TEMPERATURE_SENSOR_BINARY_v1.5.0" > firmware/TempSensor/ESP32C3/stable/Sense360-TempSensor-ESP32C3-v1.5.0-stable.bin
echo "✓ Added: firmware/TempSensor/ESP32C3/stable/Sense360-TempSensor-ESP32C3-v1.5.0-stable.bin"
echo

# Step 2: Automatically update manifest
echo "Step 2: Automatically updating manifest.json..."
python3 scripts/update-manifest.py --validate
echo

# Step 3: Show results
echo "Step 3: Verification - Current firmware in manifest:"
python3 -c "
import json
with open('manifest.json', 'r') as f:
    manifest = json.load(f)
    
print(f'Total firmware: {manifest[\"total_firmware\"]}')
print(f'Chip families: {\", \".join(manifest[\"chip_families\"])}')
print()
print('Available firmware:')
for i, build in enumerate(manifest['builds']):
    print(f'{i+1}. {build[\"device_type\"]} - {build[\"chipFamily\"]} - v{build[\"version\"]} ({build[\"channel\"]})')
"
echo

echo "=== Demo Complete ==="
echo "The ESP Web Tools installer will now automatically show all firmware options!"
echo "No manual HTML editing required - just upload the binary and everything updates automatically."