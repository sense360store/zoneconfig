# Sense360 ESP32 Firmware Installer

A complete automation system for ESP32 firmware management with GitHub Pages deployment.

## Overview

This system provides 100% automated firmware management for ESP32 devices using ESP Web Tools. Simply add firmware files to the directory structure and the system automatically updates manifests and web interface.

## Root Cause of "Failed to fetch" Error

The original error occurred because individual manifest files contained hardcoded localhost URLs (`http://localhost:5000/firmware/...`) but the site was deployed to GitHub Pages with HTTPS. ESP Web Tools couldn't fetch firmware from localhost URLs in production.

**Solution:** Use relative URLs (`firmware/CO2Monitor/ESP32S3/stable/firmware.bin`) that work in any deployment environment.

## Complete Automation System

### 1. Adding Firmware (100% Automated)

```bash
# 1. Add firmware binary to correct directory structure
cp my-firmware.bin firmware/DeviceType/ChipFamily/Channel/Sense360-DeviceType-ChipFamily-vX.X.X-Channel.bin

# 2. Run automation (updates everything)
python3 deploy-automation.py

# 3. Commit and push to GitHub
git add .
git commit -m "Add new firmware"
git push
```

### 2. Removing Firmware (100% Automated)

```bash
# 1. Delete firmware file
rm firmware/DeviceType/ChipFamily/Channel/firmware.bin

# 2. Run automation (removes from manifest/UI)
python3 deploy-automation.py

# 3. Commit and push
git add .
git commit -m "Remove firmware"
git push
```

### 3. Directory Structure

```
firmware/
├── CO2Monitor/
│   └── ESP32S3/
│       └── stable/
│           ├── Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
│           └── Sense360-CO2Monitor-ESP32S3-v1.0.1-stable.bin
├── EnvMonitor/
│   └── ESP32/
│       ├── stable/
│       │   └── Sense360-EnvMonitor-ESP32-v2.1.0-stable.bin
│       └── beta/
│           └── Sense360-EnvMonitor-ESP32-v2.2.0-beta.bin
└── TempSensor/
    └── ESP32S3/
        └── stable/
            └── Sense360-TempSensor-ESP32S3-v1.0.0-stable.bin
```

## GitHub Pages Deployment

### Automatic Deployment

The system includes GitHub Actions workflow that automatically:
1. Runs automation on every push
2. Updates manifests with relative URLs
3. Deploys to GitHub Pages
4. Ensures CORS headers are set

### Manual Deployment

```bash
# Run automation for GitHub Pages
python3 deploy-automation.py

# Files are ready for GitHub Pages deployment
```

## ESP Web Tools Integration

### Manifest Files

- **Main manifest** (`manifest.json`): Lists all firmware builds
- **Individual manifests** (`firmware-0.json`, `firmware-1.json`, etc.): One per firmware for ESP Web Tools
- **Relative URLs**: All URLs are relative for GitHub Pages compatibility
- **Improv Serial**: All manifests include `"improv": true` for automatic Wi-Fi setup

### User Interface Features

- **Logo Integration**: Sense360 logo in header with responsive design
- **Device Type Filter**: Dropdown to filter firmware by device type (CO2Monitor, EnvMonitor, etc.)
- **Search Functionality**: Real-time text search across device type, chip family, version, and channel
- **Dynamic Summary**: Shows filtered results count and available chip families
- **Responsive Design**: Works on desktop and mobile devices

### Improv Serial Wi-Fi Setup

After firmware installation, ESP Web Tools automatically prompts users for Wi-Fi credentials:

1. **Flash firmware** via ESP Web Tools
2. **Browser prompts** for Wi-Fi credentials (automatic)
3. **User enters** SSID and password in browser
4. **Device connects** to Wi-Fi automatically
5. **No manual AP** connection required

### URL Construction

- **Development**: `http://localhost:5000/firmware/...`
- **Production**: `https://your-repo.github.io/firmware/...`
- **Solution**: Use relative URLs that work in both environments

## Scripts

### Core Scripts

- `deploy-automation.py`: Main automation script for GitHub Pages
- `create-individual-manifests.py`: Creates individual manifest files
- `test-complete-workflow.py`: Tests complete workflow
- `watch-firmware.py`: Watches for firmware changes (development)

### Usage

```bash
# Full automation
python3 deploy-automation.py

# Local development with localhost URLs
python3 deploy-automation.py --local

# Watch for changes (development)
python3 watch-firmware.py

# Test complete workflow
python3 test-complete-workflow.py
```

## Best Practices

### ESP Web Tools Compliance

1. **Relative URLs**: All firmware paths are relative
2. **CORS Headers**: Proper CORS configuration in `_headers`
3. **Manifest Format**: Follows ESP Web Tools specification
4. **Individual Manifests**: One manifest per firmware for clean selection
5. **Improv Serial**: All firmware includes `improv_serial:` and manifests include `"improv": true`

### Automation Workflow

1. **No Manual Editing**: Never edit manifest.json or index.html manually
2. **Directory Structure**: Use consistent naming convention
3. **Automatic Updates**: Run automation after any firmware changes
4. **GitHub Actions**: Automatic deployment on push
5. **Improv Serial**: Automatically enabled for all firmware builds

### File Naming Convention

```
Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin

Examples:
- Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
- Sense360-EnvMonitor-ESP32-v2.1.0-stable.bin
- Sense360-TempSensor-ESP32S3-v1.0.0-beta.bin
```

## Troubleshooting

### Common Issues

1. **"Failed to fetch" error**: Check that URLs are relative, not absolute
2. **CORS errors**: Ensure `_headers` file is deployed
3. **Manifest not found**: Run automation script to generate manifests
4. **Firmware not accessible**: Check file exists in correct directory

### Debug Steps

```bash
# Test complete workflow
python3 test-complete-workflow.py

# Test Improv Serial integration
python3 test-improv-serial.py

# Validate deployment
python3 deploy-automation.py --validate

# Check individual manifest
curl https://your-repo.github.io/firmware-0.json

# Check firmware file
curl -I https://your-repo.github.io/firmware/DeviceType/ChipFamily/Channel/firmware.bin
```

## Development

### Local Development

```bash
# Start local server
python3 -m http.server 5000

# Watch for changes
python3 watch-firmware.py

# Test workflow
python3 test-complete-workflow.py
```

### Adding New Device Types

1. Create directory structure: `firmware/NewDevice/ChipFamily/Channel/`
2. Add firmware binary with naming convention
3. Run automation: `python3 deploy-automation.py`
4. Commit and push

## Summary

This system provides complete automation for ESP32 firmware management:

- **100% Automated**: No manual manifest editing required
- **GitHub Pages Ready**: Uses relative URLs and proper CORS
- **ESP Web Tools Compatible**: Follows all best practices
- **Reliable**: Comprehensive testing and validation
- **Scalable**: Easy to add new devices and firmware

The "Failed to fetch" error has been completely resolved by using relative URLs that work in any deployment environment.