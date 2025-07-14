# Automation Verification Guide

## Current System Status

### ✅ Fully Automated Features
- **Firmware Discovery**: Automatically scans `firmware/` directory
- **Metadata Extraction**: Extracts device type, chip family, version, channel from paths
- **Manifest Generation**: Creates `manifest.json` with all firmware builds
- **Individual Manifests**: Creates `firmware-N.json` for each firmware
- **Improv Serial**: Automatically includes `"improv": true` in all manifests
- **Relative URLs**: All paths work for GitHub Pages deployment
- **UI Updates**: Dynamic JavaScript loads manifests (no manual HTML editing)

### ✅ Zero Manual Editing Required
- ❌ **Never edit**: `manifest.json`, `firmware-*.json`, `index.html`
- ✅ **Always run**: `python3 deploy-automation.py` after file changes
- ✅ **Auto-generated**: All ESP Web Tools configuration

### ✅ Complete Workflow Verification

#### Adding Firmware Test
```bash
# Test adding firmware
mkdir -p firmware/TestDevice/ESP32/stable
echo "test firmware" > firmware/TestDevice/ESP32/stable/Sense360-TestDevice-ESP32-v1.0.0-stable.bin

# Run automation
python3 deploy-automation.py

# Verify results
python3 -c "
import json
with open('manifest.json') as f:
    data = json.load(f)
    print(f'Builds: {len(data[\"builds\"])}')
    for build in data['builds']:
        if build['device_type'] == 'TestDevice':
            print(f'✓ Found TestDevice v{build[\"version\"]} with improv: {build.get(\"improv\", False)}')
"

# Cleanup
rm -rf firmware/TestDevice
python3 deploy-automation.py
```

#### Removing Firmware Test
```bash
# Current firmware count
BEFORE=$(python3 -c "import json; print(len(json.load(open('manifest.json'))['builds']))")

# Remove a firmware file (temporarily)
FIRMWARE_FILE=$(find firmware -name "*.bin" | head -1)
if [ -n "$FIRMWARE_FILE" ]; then
    mv "$FIRMWARE_FILE" "$FIRMWARE_FILE.backup"
    
    # Run automation
    python3 deploy-automation.py
    
    # Check count decreased
    AFTER=$(python3 -c "import json; print(len(json.load(open('manifest.json'))['builds']))")
    
    if [ $AFTER -lt $BEFORE ]; then
        echo "✓ Removal automation working: $BEFORE → $AFTER builds"
    else
        echo "✗ Removal automation failed: $BEFORE → $AFTER builds"
    fi
    
    # Restore file
    mv "$FIRMWARE_FILE.backup" "$FIRMWARE_FILE"
    python3 deploy-automation.py
fi
```

## Manual Verification Checklist

### 📋 Before Adding Firmware
- [ ] Firmware file follows naming convention
- [ ] Directory structure is correct (4 levels deep)
- [ ] ESPHome config includes `improv_serial:`

### 📋 After Adding Firmware
- [ ] Run `python3 deploy-automation.py`
- [ ] Verify success message in output
- [ ] Check `manifest.json` includes new build
- [ ] Check individual manifest created (`firmware-N.json`)
- [ ] Verify `"improv": true` in all manifests
- [ ] Run `python3 test-complete-workflow.py`
- [ ] Test on website after deployment

### 📋 Before Removing Firmware
- [ ] Note current number of builds
- [ ] Identify which individual manifest will be removed

### 📋 After Removing Firmware
- [ ] Run `python3 deploy-automation.py`
- [ ] Verify build count decreased
- [ ] Check corresponding individual manifest removed
- [ ] Verify remaining manifests renumbered correctly
- [ ] Run `python3 test-complete-workflow.py`
- [ ] Test on website after deployment

## Automated Tests

### Complete Workflow Test
```bash
cd WebFlash
python3 test-complete-workflow.py
```

**Expected output:**
```
✓ Main page loads successfully
✓ Manifest loaded: X builds
✓ Individual manifest 0: [firmware-path]
✓ Individual manifest 1: [firmware-path]
✓ All tests passed!
```

### Improv Serial Test
```bash
cd WebFlash
python3 test-improv-serial.py
```

**Expected output:**
```
✓ PASSED: ESPHome Improv Serial Configuration
✓ PASSED: Manifest Improv Support
✓ PASSED: ESP Web Tools Compatibility
✓ PASSED: Automation Workflow
✓ ALL TESTS PASSED!
```

## Common Verification Commands

### Check Firmware Files
```bash
find firmware -name "*.bin" | sort
```

### Check Manifest Content
```bash
python3 -c "
import json
with open('manifest.json') as f:
    data = json.load(f)
    print(f'Total builds: {len(data[\"builds\"])}')
    for i, build in enumerate(data['builds']):
        print(f'{i}: {build[\"device_type\"]} v{build[\"version\"]} ({build[\"chipFamily\"]}) - improv: {build.get(\"improv\", False)}')
"
```

### Check Individual Manifests
```bash
ls -la firmware-*.json
echo "Individual manifest count: $(ls firmware-*.json | wc -l)"
```

### Verify Improv Serial Support
```bash
python3 -c "
import json
import glob

# Check all individual manifests have improv: true
for manifest_file in glob.glob('firmware-*.json'):
    with open(manifest_file) as f:
        data = json.load(f)
        improv = data['builds'][0].get('improv', False)
        print(f'{manifest_file}: improv = {improv}')
"
```

## GitHub Pages Deployment Verification

### Local Development
```bash
# Start local server
python3 -m http.server 5000

# Test in browser
open http://localhost:5000
```

### Production Deployment
```bash
# Check GitHub Actions status
# Visit: https://github.com/your-username/your-repo/actions

# Test production site
open https://your-username.github.io/your-repo/
```

## Troubleshooting Guide

### Automation Script Fails
1. Check error message in output
2. Verify firmware directory exists
3. Check file naming convention
4. Verify directory structure depth

### Manifest Missing Builds
1. Check firmware files exist
2. Verify naming convention
3. Check directory structure
4. Re-run automation script

### Individual Manifests Missing
1. Check main manifest exists
2. Verify automation completed successfully
3. Check for JSON syntax errors
4. Re-run automation script

### Improv Serial Not Working
1. Check ESPHome configs have `improv_serial:`
2. Verify manifests have `"improv": true`
3. Run `python3 test-improv-serial.py`
4. Check ESP Web Tools version compatibility

## Success Indicators

### ✅ Automation Working Correctly
- All tests pass without errors
- Firmware appears in web interface
- ESP Web Tools can install firmware
- Wi-Fi setup prompts after flashing
- No manual editing required

### ✅ GitHub Pages Deployment Working
- Site loads without errors
- Firmware dropdown populated
- Install buttons work
- Manifests accessible via direct URL
- CORS headers properly set

### ✅ Team Workflow Success
- Team members can add/remove firmware
- No knowledge of manifest format required
- No manual UI updates needed
- Consistent results across all operations

This verification system ensures **100% automation reliability** with comprehensive testing at every step.