# Fully Automated Firmware Lifecycle Management

## Overview

This system provides **100% automated firmware lifecycle management** with zero manual editing required. Simply add or remove firmware files and run the automation script - all manifests and UI updates happen automatically.

## 🚀 Adding New Firmware

### Step 1: File Placement and Naming

**Location:** Place firmware files in the structured directory:
```
firmware/[DeviceType]/[ChipFamily]/[Channel]/[FileName].bin
```

**Naming Convention:**
```
Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin
```

**Examples:**
```
firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.2.0-stable.bin
firmware/TempSensor/ESP32/beta/Sense360-TempSensor-ESP32-v1.0.0-beta.bin
firmware/EnvMonitor/ESP32S2/stable/Sense360-EnvMonitor-ESP32S2-v2.0.0-stable.bin
```

### Step 2: Run Automation

```bash
cd WebFlash
python3 deploy-automation.py
```

**What happens automatically:**
- Scans firmware/ directory for all .bin files
- Extracts metadata from directory structure and filename
- Updates manifest.json with new firmware entry
- Creates individual manifest file (firmware-N.json) for ESP Web Tools
- Adds "improv": true to all manifests for Wi-Fi setup
- Updates web interface with new firmware option
- Validates all files and URLs

### Step 3: Deploy to GitHub Pages

```bash
git add .
git commit -m "Add [DeviceType] v[Version] firmware"
git push origin main
```

**GitHub Actions automatically:**
- Runs deploy-automation.py on push
- Updates GitHub Pages with new firmware
- Serves updated manifests and UI

### Step 4: Verification Checklist

✅ **File Structure Check:**
```bash
ls -la firmware/[DeviceType]/[ChipFamily]/[Channel]/
```

✅ **Manifest Verification:**
```bash
python3 -c "
import json
with open('manifest.json') as f:
    data = json.load(f)
    print(f'Total builds: {len(data[\"builds\"])}')
    for build in data['builds']:
        print(f'  {build[\"device_type\"]} v{build[\"version\"]} ({build[\"chipFamily\"]})')
"
```

✅ **Individual Manifest Check:**
```bash
ls -la firmware-*.json
```

✅ **Complete Workflow Test:**
```bash
python3 test-complete-workflow.py
```

✅ **Improv Serial Test:**
```bash
python3 test-improv-serial.py
```

✅ **Web Interface Check:**
- Open https://your-repo.github.io/
- Verify new firmware appears in dropdown
- Verify install button works
- Verify ESP Web Tools loads correct manifest

## 🗑️ Removing Firmware

### Step 1: Delete Firmware File

```bash
rm firmware/[DeviceType]/[ChipFamily]/[Channel]/[FileName].bin
```

### Step 2: Run Automation

```bash
cd WebFlash
python3 deploy-automation.py
```

**What happens automatically:**
- Scans firmware/ directory (missing file not found)
- Removes entry from manifest.json
- Removes corresponding individual manifest file
- Updates web interface (firmware no longer appears)
- Renumbers remaining individual manifests

### Step 3: Deploy Changes

```bash
git add .
git commit -m "Remove [DeviceType] v[Version] firmware"
git push origin main
```

### Step 4: Verification Checklist

✅ **File Removal Check:**
```bash
ls -la firmware/[DeviceType]/[ChipFamily]/[Channel]/
```

✅ **Manifest Verification:**
```bash
python3 -c "
import json
with open('manifest.json') as f:
    data = json.load(f)
    print(f'Total builds: {len(data[\"builds\"])}')
    for build in data['builds']:
        print(f'  {build[\"device_type\"]} v{build[\"version\"]} ({build[\"chipFamily\"]})')
"
```

✅ **Individual Manifest Cleanup:**
```bash
ls -la firmware-*.json
```

✅ **Web Interface Check:**
- Verify removed firmware no longer appears
- Verify remaining firmware still works

## 🔄 Directory Structure Examples

### Supported Chip Families
- `ESP32` → Maps to `ESP32`
- `ESP32S2` → Maps to `ESP32-S2`
- `ESP32S3` → Maps to `ESP32-S3`
- `ESP32C3` → Maps to `ESP32-C3`
- `ESP32C6` → Maps to `ESP32-C6`
- `ESP32H2` → Maps to `ESP32-H2`

### Supported Channels
- `stable` → Production-ready firmware
- `beta` → Pre-release firmware
- `alpha` → Development firmware

### Complete Directory Example
```
firmware/
├── CO2Monitor/
│   ├── ESP32S3/
│   │   ├── stable/
│   │   │   ├── Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
│   │   │   └── Sense360-CO2Monitor-ESP32S3-v1.1.0-stable.bin
│   │   └── beta/
│   │       └── Sense360-CO2Monitor-ESP32S3-v1.2.0-beta.bin
│   └── ESP32/
│       └── stable/
│           └── Sense360-CO2Monitor-ESP32-v1.0.0-stable.bin
├── EnvMonitor/
│   ├── ESP32/
│   │   ├── stable/
│   │   │   └── Sense360-EnvMonitor-ESP32-v2.1.0-stable.bin
│   │   └── beta/
│   │       └── Sense360-EnvMonitor-ESP32-v2.2.0-beta.bin
│   └── ESP32S2/
│       └── stable/
│           └── Sense360-EnvMonitor-ESP32S2-v2.0.0-stable.bin
└── TempSensor/
    └── ESP32S3/
        └── stable/
            └── Sense360-TempSensor-ESP32S3-v1.0.0-stable.bin
```

## 📋 Quick Reference Checklists

### ✅ Adding Firmware Checklist
1. [ ] Place .bin file in correct directory structure
2. [ ] Use proper naming convention
3. [ ] Run `python3 deploy-automation.py`
4. [ ] Verify automation output shows new firmware
5. [ ] Run `python3 test-complete-workflow.py`
6. [ ] Commit and push to GitHub
7. [ ] Verify on GitHub Pages site

### ✅ Removing Firmware Checklist
1. [ ] Delete .bin file from firmware directory
2. [ ] Run `python3 deploy-automation.py`
3. [ ] Verify automation output shows removal
4. [ ] Run `python3 test-complete-workflow.py`
5. [ ] Commit and push to GitHub
6. [ ] Verify removed from GitHub Pages site

### ✅ Automation Verification Checklist
1. [ ] All tests pass: `python3 test-complete-workflow.py`
2. [ ] Improv Serial works: `python3 test-improv-serial.py`
3. [ ] Manifest files exist: `ls firmware-*.json`
4. [ ] Web interface loads: Open site and check dropdown
5. [ ] ESP Web Tools works: Test firmware installation

## 🚫 Zero Manual Editing Required

### Files That Are NEVER Edited Manually:
- ✅ `manifest.json` - Always generated by automation
- ✅ `firmware-*.json` - Always generated by automation
- ✅ `index.html` - Dynamic JavaScript loads manifests
- ✅ Any UI components - All data comes from manifests

### Files That CAN Be Edited:
- ✅ `deploy-automation.py` - Automation script improvements
- ✅ `create-individual-manifests.py` - Individual manifest generation
- ✅ `README.md` - Documentation updates
- ✅ `css/style.css` - UI styling changes
- ✅ ESPHome YAML files - Firmware configuration

### If Manual Editing Seems Necessary:
1. **Check automation**: Run `python3 deploy-automation.py`
2. **Check tests**: Run `python3 test-complete-workflow.py`
3. **Check naming**: Verify directory structure and filename
4. **Check logs**: Look for error messages in automation output
5. **Fix automation**: Update scripts instead of editing manifests

## 🔧 Advanced Automation Features

### Automatic Improv Serial Support
- All firmware automatically includes `improv_serial:` in ESPHome configs
- All manifests automatically include `"improv": true`
- ESP Web Tools automatically prompts for Wi-Fi after flashing

### Relative URL Generation
- All URLs are relative for GitHub Pages compatibility
- Works in development (`localhost:5000`) and production
- No hardcoded URLs in any manifest files

### Comprehensive Validation
- File existence checks
- URL accessibility tests
- Manifest format validation
- ESP Web Tools compatibility verification

## 🎯 Team Workflow Summary

**For any team member to add firmware:**
1. Drop .bin file in correct directory
2. Run automation script
3. Commit and push

**For any team member to remove firmware:**
1. Delete .bin file
2. Run automation script
3. Commit and push

**No special knowledge required:**
- No manifest editing
- No UI changes
- No ESP Web Tools configuration
- No manual URL updates

**Everything is automated:**
- Manifest generation
- UI updates
- Improv Serial support
- GitHub Pages deployment

## 🚨 Troubleshooting

### Common Issues and Solutions

**Issue:** Firmware not appearing in UI
**Solution:** Check naming convention and directory structure

**Issue:** ESP Web Tools "Failed to fetch"
**Solution:** Verify relative URLs in manifests (automation handles this)

**Issue:** Wi-Fi setup not working
**Solution:** Check ESPHome config has `improv_serial:` and manifest has `"improv": true`

**Issue:** Multiple firmware versions
**Solution:** Use different version numbers in filenames

**Issue:** Automation script fails
**Solution:** Check firmware directory exists and contains .bin files

### Debug Commands
```bash
# Check automation output
python3 deploy-automation.py

# Validate complete workflow
python3 test-complete-workflow.py

# Test Improv Serial integration
python3 test-improv-serial.py

# Check manifest contents
cat manifest.json | python3 -m json.tool

# Check individual manifests
ls firmware-*.json && cat firmware-0.json | python3 -m json.tool
```

## ✅ Success Confirmation

The automation system is working correctly when:
- All tests pass without errors
- Web interface shows expected firmware options
- ESP Web Tools can flash firmware successfully
- Wi-Fi setup prompts appear after flashing
- No manual editing was required

This system provides **100% automated firmware lifecycle management** with zero manual intervention required for adding, removing, or updating firmware builds.