# Team Workflow Guide: Zero-Touch Firmware Management

## Quick Start for Team Members

### 🎯 The Simple Truth
**Never edit manifest.json, index.html, or any UI files manually.**
**Just add/remove firmware files and run one script.**

## 📁 Adding New Firmware

### Step 1: Drop the File
```bash
# Copy your firmware binary to the correct location
cp your-firmware.bin firmware/[DeviceType]/[ChipFamily]/[Channel]/Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin
```

**Examples:**
```bash
# CO2 Monitor for ESP32-S3, stable release
cp co2-monitor.bin firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.5.0-stable.bin

# Temperature Sensor for ESP32, beta release
cp temp-sensor.bin firmware/TempSensor/ESP32/beta/Sense360-TempSensor-ESP32-v2.0.0-beta.bin
```

### Step 2: Run Automation
```bash
cd WebFlash
python3 deploy-automation.py
```

**Expected output:**
```
🧹 Cleaning up X existing manifest files...
📦 Found: Sense360-CO2Monitor-ESP32S3-v1.5.0-stable.bin
📅 Using git commit date: 2025-07-13T14:25:36Z
✓ Created manifest.json with X builds
✓ Created firmware-N.json for CO2Monitor v1.5.0
✅ CLEAN STATE AUTOMATION COMPLETED
```

### Step 3: Deploy
```bash
git add .
git commit -m "Add CO2Monitor v1.5.0 firmware"
git push origin main
```

### Step 4: Verify (2 minutes)
1. Open https://your-repo.github.io/
2. Check new firmware appears in dropdown
3. Click install button to test ESP Web Tools

**✅ Done! No manual editing required.**

## 🗑️ Removing Firmware

### Step 1: Delete the File
```bash
rm firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.4.0-stable.bin
```

### Step 2: Run Automation
```bash
cd WebFlash
python3 deploy-automation.py
```

**Expected output:**
```
🧹 Cleaning up X existing manifest files...
📦 Found: X builds (1 fewer than before)
✅ CLEAN STATE AUTOMATION COMPLETED
✓ Perfect synchronization between firmware/ directory and manifests
```

### Step 3: Deploy
```bash
git add .
git commit -m "Remove CO2Monitor v1.4.0 firmware"
git push origin main
```

**✅ Done! Firmware removed from site automatically.**

## 📋 Directory Structure Reference

### Required Structure
```
firmware/
└── [DeviceType]/
    └── [ChipFamily]/
        └── [Channel]/
            └── Sense360-[DeviceType]-[ChipFamily]-v[Version]-[Channel].bin
```

### Device Types
- `CO2Monitor` - CO2 monitoring devices
- `EnvMonitor` - Environmental monitoring devices
- `TempSensor` - Temperature sensors
- `HumiditySensor` - Humidity sensors
- `AirQualitySensor` - Air quality monitors

### Chip Families
- `ESP32` - Original ESP32
- `ESP32S2` - ESP32-S2 variant
- `ESP32S3` - ESP32-S3 variant
- `ESP32C3` - ESP32-C3 variant
- `ESP32C6` - ESP32-C6 variant
- `ESP32H2` - ESP32-H2 variant

### Channels
- `stable` - Production firmware
- `beta` - Pre-release firmware
- `alpha` - Development firmware

## 🚨 Common Mistakes to Avoid

### ❌ Wrong File Placement
```bash
# DON'T do this
firmware/my-firmware.bin

# DO this instead
firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
```

### ❌ Wrong Naming Convention
```bash
# DON'T do this
Sense360-v1.0.0.bin
co2-monitor-esp32s3.bin

# DO this instead
Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
```

### ❌ Manual Editing
```bash
# DON'T edit these files manually
manifest.json
firmware-*.json
index.html

# DO run automation instead
python3 deploy-automation.py
```

### ❌ Forgetting to Run Automation
```bash
# DON'T just commit the firmware file
git add firmware/
git commit -m "Add firmware"

# DO run automation first
python3 deploy-automation.py
git add .
git commit -m "Add firmware"
```

## 🔍 Verification Commands

### Check Your Work
```bash
# See all firmware files
find firmware/ -name "*.bin" | sort

# Check manifest has correct number of builds
python3 -c "
import json
with open('manifest.json') as f:
    data = json.load(f)
    print(f'Total builds: {len(data[\"builds\"])}')
    for build in data['builds']:
        print(f'  {build[\"device_type\"]} v{build[\"version\"]} - {build[\"build_date\"]}')
"

# Test complete workflow
python3 test-complete-workflow.py

# Test clean state automation
python3 test-clean-state-automation.py
```

## 📞 Getting Help

### If Something Goes Wrong

1. **Check the error message** from automation script
2. **Verify file naming** follows exact convention
3. **Check directory structure** matches requirements
4. **Run test script** to identify issues:
   ```bash
   python3 test-complete-workflow.py
   ```

### Common Error Messages

**"No firmware files found"**
- Check directory structure
- Verify files end with `.bin`
- Ensure correct path: `firmware/DeviceType/ChipFamily/Channel/`

**"Failed to extract metadata"**
- Check filename follows naming convention
- Verify directory structure depth (4 levels)

**"Manifest validation failed"**
- Re-run automation script
- Check for JSON syntax errors (automation should prevent this)

## 🎯 Success Criteria

Your workflow is working correctly when:
- ✅ Automation script runs without errors
- ✅ Orphaned manifest files are cleaned up automatically
- ✅ Build dates show accurate git commit or file timestamps
- ✅ Test script passes all checks
- ✅ Website shows your firmware in dropdown
- ✅ ESP Web Tools can install firmware
- ✅ Wi-Fi setup prompts appear after flashing
- ✅ You never edited any manifest or UI files

## 🚀 Advanced Tips

### Multiple Versions
```bash
# Keep multiple versions of same device type
firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.0.0-stable.bin
firmware/CO2Monitor/ESP32S3/stable/Sense360-CO2Monitor-ESP32S3-v1.1.0-stable.bin
firmware/CO2Monitor/ESP32S3/beta/Sense360-CO2Monitor-ESP32S3-v1.2.0-beta.bin
```

### Batch Operations
```bash
# Add multiple firmware files at once
cp *.bin firmware/CO2Monitor/ESP32S3/stable/
python3 deploy-automation.py  # Processes all files
```

### Development Workflow
```bash
# For active development
python3 watch-firmware.py  # Auto-runs automation on file changes
```

## 📊 Team Responsibilities

### Firmware Developer
1. Build firmware binary
2. Place in correct directory with proper naming
3. Run automation script
4. Test on website
5. Commit and push

### QA Tester
1. Verify firmware appears on website
2. Test ESP Web Tools installation
3. Test Wi-Fi setup functionality
4. Validate device behavior

### DevOps/Deployment
1. Monitor GitHub Actions
2. Verify GitHub Pages deployment
3. Check automation script health
4. Update documentation as needed

## 🔄 Continuous Integration

### GitHub Actions Workflow
- Automatically runs on every push
- Executes `python3 deploy-automation.py`
- Deploys to GitHub Pages
- No manual intervention required

### Monitoring
- Check GitHub Actions tab for deployment status
- Monitor website for firmware availability
- Test ESP Web Tools functionality regularly

This workflow ensures **zero manual editing** and **100% automation** for firmware lifecycle management.