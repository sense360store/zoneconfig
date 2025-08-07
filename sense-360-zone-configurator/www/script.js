// Sense 360 Zone Configurator
// Main application logic for mmWave sensor zone configuration

class Sense360Configurator {
    constructor() {
        this.selectedDevice = null;
        this.entities = {};
        this.zones = [];
        this.targets = [];
        this.canvas = null;
        this.ctx = null;
        this.isDragging = false;
        this.selectedZone = null;
        this.ws = null;
        this.wsReconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.init();
    }

    async init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.setupWebSocket();
        await this.loadDevices();
        this.startRealTimeUpdates();
    }

    setupCanvas() {
        this.canvas = document.getElementById('visualizationCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Set canvas size
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth - 20;
        this.canvas.height = Math.min(600, container.clientWidth * 0.6);
        
        this.drawVisualization();
    }

    setupEventListeners() {
        // Device selection
        document.getElementById('deviceSelect').addEventListener('change', (e) => {
            this.selectDevice(e.target.value);
        });

        // Canvas events
        this.canvas.addEventListener('mousedown', this.handleCanvasMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleCanvasMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleCanvasMouseUp.bind(this));

        // Control buttons
        document.getElementById('addZoneBtn').addEventListener('click', () => this.addZone());
        document.getElementById('clearZonesBtn').addEventListener('click', () => this.clearAllZones());
        document.getElementById('refreshBtn').addEventListener('click', () => this.loadDevices());
        document.getElementById('updateZoneBtn').addEventListener('click', () => this.updateSelectedZone());
        document.getElementById('deleteZoneBtn').addEventListener('click', () => this.deleteSelectedZone());

        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettings());

        // Real-time toggle
        document.getElementById('realTimeToggle').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.startRealTimeUpdates();
            } else {
                this.stopRealTimeUpdates();
            }
        });

        // Zone property inputs
        ['zoneName', 'zoneOffDelay', 'zoneX1', 'zoneY1', 'zoneX2', 'zoneY2'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => this.updateZonePreview());
        });

        // Window resize
        window.addEventListener('resize', () => {
            this.setupCanvas();
        });
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.wsReconnectAttempts = 0;
            this.updateConnectionStatus(true);
            
            // Subscribe to state changes
            this.ws.send(JSON.stringify({
                id: 1,
                type: 'subscribe_events',
                event_type: 'state_changed'
            }));
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    attemptReconnect() {
        if (this.wsReconnectAttempts < this.maxReconnectAttempts) {
            this.wsReconnectAttempts++;
            console.log(`Attempting WebSocket reconnection ${this.wsReconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => this.setupWebSocket(), 5000 * this.wsReconnectAttempts);
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'event' && data.event?.event_type === 'state_changed') {
            const entityId = data.event.data.entity_id;
            const newState = data.event.data.new_state;
            
            if (newState && this.isRelevantEntity(entityId)) {
                this.entities[entityId] = newState;
                this.updateVisualization();
                this.updateLastUpdateTime();
            }
        }
    }

    isRelevantEntity(entityId) {
        if (!entityId || !this.selectedDevice) return false;
        
        const relevantSuffixes = [
            'target_1_x', 'target_1_y', 'target_1_active',
            'target_2_x', 'target_2_y', 'target_2_active',
            'target_3_x', 'target_3_y', 'target_3_active',
            'zone_1_begin_x', 'zone_1_begin_y', 'zone_1_end_x', 'zone_1_end_y',
            'zone_2_begin_x', 'zone_2_begin_y', 'zone_2_end_x', 'zone_2_end_y',
            'zone_3_begin_x', 'zone_3_begin_y', 'zone_3_end_x', 'zone_3_end_y',
            'zone_4_begin_x', 'zone_4_begin_y', 'zone_4_end_x', 'zone_4_end_y'
        ];
        
        return relevantSuffixes.some(suffix => entityId.endsWith(suffix)) &&
               entityId.startsWith(this.selectedDevice);
    }

    async loadDevices() {
        try {
            const template = `
                {%- set devices = states | selectattr('entity_id', 'match', '.*zone_1_begin_x$') | map(attribute='entity_id') | map('regex_replace', '_zone_1_begin_x$', '') | list -%}
                {{ devices | to_json }}
            `;
            
            const response = await fetch('/api/template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ template })
            });
            
            if (response.ok) {
                const devices = await response.json();
                this.populateDeviceSelect(devices);
            } else {
                console.error('Failed to load devices:', response.statusText);
                this.showError('Failed to load mmWave devices');
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            this.showError('Error connecting to Home Assistant');
        }
    }

    populateDeviceSelect(devices) {
        const select = document.getElementById('deviceSelect');
        select.innerHTML = '<option value="">Select a sensor device...</option>';
        
        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device;
            option.textContent = device.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            select.appendChild(option);
        });
    }

    async selectDevice(deviceId) {
        if (!deviceId) {
            this.selectedDevice = null;
            this.entities = {};
            this.zones = [];
            this.targets = [];
            this.updateVisualization();
            return;
        }

        this.selectedDevice = deviceId;
        await this.loadDeviceEntities();
        this.loadZonesFromEntities();
        this.updateVisualization();
        this.updateZoneList();
    }

    async loadDeviceEntities() {
        if (!this.selectedDevice) return;

        const entitySuffixes = [
            'zone_1_begin_x', 'zone_1_begin_y', 'zone_1_end_x', 'zone_1_end_y',
            'zone_2_begin_x', 'zone_2_begin_y', 'zone_2_end_x', 'zone_2_end_y',
            'zone_3_begin_x', 'zone_3_begin_y', 'zone_3_end_x', 'zone_3_end_y',
            'zone_4_begin_x', 'zone_4_begin_y', 'zone_4_end_x', 'zone_4_end_y',
            'target_1_x', 'target_1_y', 'target_1_active',
            'target_2_x', 'target_2_y', 'target_2_active',
            'target_3_x', 'target_3_y', 'target_3_active',
            'zone_1_off_delay', 'zone_2_off_delay', 'zone_3_off_delay', 'zone_4_off_delay'
        ];

        for (const suffix of entitySuffixes) {
            const entityId = `${this.selectedDevice}_${suffix}`;
            try {
                const response = await fetch(`/api/entities/${entityId}`);
                if (response.ok) {
                    const entity = await response.json();
                    this.entities[entityId] = entity;
                }
            } catch (error) {
                console.error(`Error loading entity ${entityId}:`, error);
            }
        }
    }

    loadZonesFromEntities() {
        this.zones = [];
        
        for (let i = 1; i <= 4; i++) {
            const beginX = this.getEntityValue(`${this.selectedDevice}_zone_${i}_begin_x`);
            const beginY = this.getEntityValue(`${this.selectedDevice}_zone_${i}_begin_y`);
            const endX = this.getEntityValue(`${this.selectedDevice}_zone_${i}_end_x`);
            const endY = this.getEntityValue(`${this.selectedDevice}_zone_${i}_end_y`);
            const offDelay = this.getEntityValue(`${this.selectedDevice}_zone_${i}_off_delay`) || 5;

            if (beginX !== null && beginY !== null && endX !== null && endY !== null) {
                this.zones.push({
                    id: i,
                    name: `Zone ${i}`,
                    x1: parseInt(beginX),
                    y1: parseInt(beginY),
                    x2: parseInt(endX),
                    y2: parseInt(endY),
                    offDelay: parseInt(offDelay),
                    color: this.getZoneColor(i)
                });
            }
        }
    }

    getEntityValue(entityId) {
        const entity = this.entities[entityId];
        return entity ? parseFloat(entity.state) : null;
    }

    getZoneColor(zoneId) {
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];
        return colors[(zoneId - 1) % colors.length];
    }

    drawVisualization() {
        if (!this.ctx) return;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw background grid
        this.drawGrid();

        // Draw sensor range circle
        this.drawSensorRange();

        // Draw zones
        this.zones.forEach(zone => this.drawZone(zone));

        // Draw targets
        this.updateTargets();
        this.targets.forEach(target => this.drawTarget(target));

        // Draw coordinate system
        this.drawCoordinateSystem();
    }

    drawGrid() {
        const gridSize = 20;
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 0.5;

        for (let x = 0; x <= this.canvas.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }

        for (let y = 0; y <= this.canvas.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }

    drawSensorRange() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height - 50;
        const maxDistance = this.getEntityValue(`${this.selectedDevice}_max_distance`) || 6000;
        const scale = Math.min(this.canvas.width, this.canvas.height) / (maxDistance * 2);
        const radius = maxDistance * scale;

        this.ctx.strokeStyle = '#666';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        this.ctx.stroke();

        // Draw sensor position
        this.ctx.fillStyle = '#FF4444';
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, 5, 0, 2 * Math.PI);
        this.ctx.fill();
    }

    drawZone(zone) {
        const coords = this.mmwaveToCanvas(zone.x1, zone.y1, zone.x2, zone.y2);
        
        // Draw zone rectangle
        this.ctx.fillStyle = zone.color + '40';
        this.ctx.strokeStyle = zone.color;
        this.ctx.lineWidth = zone === this.selectedZone ? 3 : 2;
        
        this.ctx.fillRect(coords.x, coords.y, coords.width, coords.height);
        this.ctx.strokeRect(coords.x, coords.y, coords.width, coords.height);

        // Draw zone label
        this.ctx.fillStyle = zone.color;
        this.ctx.font = '14px Arial';
        this.ctx.fillText(zone.name, coords.x + 5, coords.y + 20);
    }

    drawTarget(target) {
        const coords = this.mmwaveToCanvas(target.x, target.y);
        
        this.ctx.fillStyle = '#00FF00';
        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 2;
        
        this.ctx.beginPath();
        this.ctx.arc(coords.x, coords.y, 8, 0, 2 * Math.PI);
        this.ctx.fill();
        this.ctx.stroke();

        // Draw target label
        this.ctx.fillStyle = '#FFFFFF';
        this.ctx.font = '12px Arial';
        this.ctx.fillText(`T${target.id}`, coords.x + 12, coords.y + 4);
    }

    drawCoordinateSystem() {
        // Draw axes
        this.ctx.strokeStyle = '#888';
        this.ctx.lineWidth = 1;
        
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height - 50;
        
        // X-axis
        this.ctx.beginPath();
        this.ctx.moveTo(50, centerY);
        this.ctx.lineTo(this.canvas.width - 50, centerY);
        this.ctx.stroke();
        
        // Y-axis
        this.ctx.beginPath();
        this.ctx.moveTo(centerX, 50);
        this.ctx.lineTo(centerX, this.canvas.height - 50);
        this.ctx.stroke();

        // Labels
        this.ctx.fillStyle = '#AAA';
        this.ctx.font = '12px Arial';
        this.ctx.fillText('X', this.canvas.width - 40, centerY - 10);
        this.ctx.fillText('Y', centerX + 10, 40);
    }

    mmwaveToCanvas(x1, y1, x2 = null, y2 = null) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height - 50;
        const scale = Math.min(this.canvas.width, this.canvas.height) / 12000; // Scale for mmWave coordinates

        if (x2 !== null && y2 !== null) {
            // Rectangle coordinates
            const canvasX1 = centerX + x1 * scale;
            const canvasY1 = centerY - y1 * scale;
            const canvasX2 = centerX + x2 * scale;
            const canvasY2 = centerY - y2 * scale;
            
            return {
                x: Math.min(canvasX1, canvasX2),
                y: Math.min(canvasY1, canvasY2),
                width: Math.abs(canvasX2 - canvasX1),
                height: Math.abs(canvasY2 - canvasY1)
            };
        } else {
            // Point coordinates
            return {
                x: centerX + x1 * scale,
                y: centerY - y1 * scale
            };
        }
    }

    canvasToMmwave(canvasX, canvasY) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height - 50;
        const scale = Math.min(this.canvas.width, this.canvas.height) / 12000;

        return {
            x: Math.round((canvasX - centerX) / scale),
            y: Math.round((centerY - canvasY) / scale)
        };
    }

    updateTargets() {
        this.targets = [];
        
        for (let i = 1; i <= 3; i++) {
            const active = this.getEntityValue(`${this.selectedDevice}_target_${i}_active`);
            const x = this.getEntityValue(`${this.selectedDevice}_target_${i}_x`);
            const y = this.getEntityValue(`${this.selectedDevice}_target_${i}_y`);

            if (active && x !== null && y !== null) {
                this.targets.push({
                    id: i,
                    x: parseFloat(x),
                    y: parseFloat(y),
                    active: true
                });
            }
        }

        this.updateTargetList();
    }

    updateTargetList() {
        const targetList = document.getElementById('targetList');
        
        if (this.targets.length === 0) {
            targetList.innerHTML = `
                <div class="text-muted text-center py-2">
                    <i class="fas fa-crosshairs"></i>
                    <p class="mb-0">No targets detected</p>
                </div>
            `;
            return;
        }

        targetList.innerHTML = this.targets.map(target => `
            <div class="d-flex justify-content-between align-items-center py-1">
                <span><i class="fas fa-dot-circle text-success"></i> Target ${target.id}</span>
                <span class="text-muted">(${target.x}, ${target.y})</span>
            </div>
        `).join('');
    }

    handleCanvasMouseDown(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Check if clicking on existing zone
        const clickedZone = this.getZoneAtPosition(x, y);
        if (clickedZone) {
            this.selectZone(clickedZone);
            return;
        }

        // Start creating new zone
        this.isDragging = true;
        this.dragStart = { x, y };
    }

    handleCanvasMouseMove(event) {
        if (!this.isDragging) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Draw temporary zone preview
        this.drawVisualization();
        
        const tempCoords = {
            x: Math.min(this.dragStart.x, x),
            y: Math.min(this.dragStart.y, y),
            width: Math.abs(x - this.dragStart.x),
            height: Math.abs(y - this.dragStart.y)
        };

        this.ctx.strokeStyle = '#FFFFFF';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.strokeRect(tempCoords.x, tempCoords.y, tempCoords.width, tempCoords.height);
        this.ctx.setLineDash([]);
    }

    handleCanvasMouseUp(event) {
        if (!this.isDragging) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        // Only create zone if dragged area is large enough
        if (Math.abs(x - this.dragStart.x) > 20 && Math.abs(y - this.dragStart.y) > 20) {
            this.createZoneFromDrag(this.dragStart.x, this.dragStart.y, x, y);
        }

        this.isDragging = false;
        this.dragStart = null;
        this.drawVisualization();
    }

    getZoneAtPosition(canvasX, canvasY) {
        return this.zones.find(zone => {
            const coords = this.mmwaveToCanvas(zone.x1, zone.y1, zone.x2, zone.y2);
            return canvasX >= coords.x && canvasX <= coords.x + coords.width &&
                   canvasY >= coords.y && canvasY <= coords.y + coords.height;
        });
    }

    createZoneFromDrag(x1, y1, x2, y2) {
        const mmwaveStart = this.canvasToMmwave(x1, y1);
        const mmwaveEnd = this.canvasToMmwave(x2, y2);

        const availableZoneId = this.getNextAvailableZoneId();
        if (!availableZoneId) {
            this.showError('Maximum number of zones (4) reached');
            return;
        }

        const newZone = {
            id: availableZoneId,
            name: `Zone ${availableZoneId}`,
            x1: Math.min(mmwaveStart.x, mmwaveEnd.x),
            y1: Math.min(mmwaveStart.y, mmwaveEnd.y),
            x2: Math.max(mmwaveStart.x, mmwaveEnd.x),
            y2: Math.max(mmwaveStart.y, mmwaveEnd.y),
            offDelay: 5,
            color: this.getZoneColor(availableZoneId)
        };

        this.zones.push(newZone);
        this.selectZone(newZone);
        this.updateZoneList();
        this.saveZoneToDevice(newZone);
    }

    getNextAvailableZoneId() {
        for (let i = 1; i <= 4; i++) {
            if (!this.zones.find(zone => zone.id === i)) {
                return i;
            }
        }
        return null;
    }

    selectZone(zone) {
        this.selectedZone = zone;
        this.showZoneProperties(zone);
        this.drawVisualization();
    }

    showZoneProperties(zone) {
        document.getElementById('zoneProperties').classList.remove('d-none');
        document.getElementById('zoneName').value = zone.name;
        document.getElementById('zoneOffDelay').value = zone.offDelay;
        document.getElementById('zoneX1').value = zone.x1;
        document.getElementById('zoneY1').value = zone.y1;
        document.getElementById('zoneX2').value = zone.x2;
        document.getElementById('zoneY2').value = zone.y2;
    }

    updateZoneList() {
        const zoneList = document.getElementById('zoneList');
        
        if (this.zones.length === 0) {
            zoneList.innerHTML = `
                <div class="text-muted text-center py-3">
                    <i class="fas fa-vector-square fa-2x mb-2"></i>
                    <p class="mb-0">No zones configured</p>
                    <small>Add zones using the canvas</small>
                </div>
            `;
            return;
        }

        zoneList.innerHTML = this.zones.map(zone => `
            <div class="list-group-item list-group-item-action bg-dark text-light d-flex justify-content-between align-items-center ${zone === this.selectedZone ? 'active' : ''}"
                 onclick="app.selectZone(app.zones.find(z => z.id === ${zone.id}))">
                <div>
                    <i class="fas fa-square" style="color: ${zone.color}"></i>
                    <span class="ms-2">${zone.name}</span>
                </div>
                <small class="text-muted">
                    (${zone.x1}, ${zone.y1}) → (${zone.x2}, ${zone.y2})
                </small>
            </div>
        `).join('');
    }

    async saveZoneToDevice(zone) {
        if (!this.selectedDevice) return;

        const entityPrefix = `${this.selectedDevice}_zone_${zone.id}`;
        
        try {
            await Promise.all([
                this.setEntityValue(`${entityPrefix}_begin_x`, zone.x1),
                this.setEntityValue(`${entityPrefix}_begin_y`, zone.y1),
                this.setEntityValue(`${entityPrefix}_end_x`, zone.x2),
                this.setEntityValue(`${entityPrefix}_end_y`, zone.y2),
                this.setEntityValue(`${entityPrefix}_off_delay`, zone.offDelay)
            ]);
            
            this.showSuccess(`Zone ${zone.id} saved successfully`);
        } catch (error) {
            console.error('Error saving zone:', error);
            this.showError(`Failed to save zone ${zone.id}`);
        }
    }

    async setEntityValue(entityId, value) {
        const response = await fetch('/api/services/number/set_value', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entity_id: entityId, value })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to set ${entityId} to ${value}`);
        }
    }

    async updateSelectedZone() {
        if (!this.selectedZone) return;

        const zone = this.selectedZone;
        zone.name = document.getElementById('zoneName').value;
        zone.offDelay = parseInt(document.getElementById('zoneOffDelay').value);
        zone.x1 = parseInt(document.getElementById('zoneX1').value);
        zone.y1 = parseInt(document.getElementById('zoneY1').value);
        zone.x2 = parseInt(document.getElementById('zoneX2').value);
        zone.y2 = parseInt(document.getElementById('zoneY2').value);

        await this.saveZoneToDevice(zone);
        this.updateZoneList();
        this.drawVisualization();
    }

    deleteSelectedZone() {
        if (!this.selectedZone) return;

        const zoneIndex = this.zones.findIndex(z => z.id === this.selectedZone.id);
        if (zoneIndex !== -1) {
            this.zones.splice(zoneIndex, 1);
            this.clearZoneFromDevice(this.selectedZone.id);
            this.selectedZone = null;
            document.getElementById('zoneProperties').classList.add('d-none');
            this.updateZoneList();
            this.drawVisualization();
        }
    }

    async clearZoneFromDevice(zoneId) {
        if (!this.selectedDevice) return;

        const entityPrefix = `${this.selectedDevice}_zone_${zoneId}`;
        
        try {
            await Promise.all([
                this.setEntityValue(`${entityPrefix}_begin_x`, 0),
                this.setEntityValue(`${entityPrefix}_begin_y`, 0),
                this.setEntityValue(`${entityPrefix}_end_x`, 0),
                this.setEntityValue(`${entityPrefix}_end_y`, 0)
            ]);
        } catch (error) {
            console.error('Error clearing zone:', error);
        }
    }

    addZone() {
        const availableZoneId = this.getNextAvailableZoneId();
        if (!availableZoneId) {
            this.showError('Maximum number of zones (4) reached');
            return;
        }

        const newZone = {
            id: availableZoneId,
            name: `Zone ${availableZoneId}`,
            x1: -1000,
            y1: 1000,
            x2: 1000,
            y2: 2000,
            offDelay: 5,
            color: this.getZoneColor(availableZoneId)
        };

        this.zones.push(newZone);
        this.selectZone(newZone);
        this.updateZoneList();
        this.saveZoneToDevice(newZone);
        this.drawVisualization();
    }

    clearAllZones() {
        if (this.zones.length === 0) return;

        if (confirm('Are you sure you want to clear all zones? This action cannot be undone.')) {
            this.zones.forEach(zone => this.clearZoneFromDevice(zone.id));
            this.zones = [];
            this.selectedZone = null;
            document.getElementById('zoneProperties').classList.add('d-none');
            this.updateZoneList();
            this.drawVisualization();
        }
    }

    async openSettings() {
        const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
        const content = document.getElementById('settingsContent');
        
        content.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading settings...</p>
            </div>
        `;
        
        modal.show();
        
        if (!this.selectedDevice) {
            content.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please select a device first to access settings.
                </div>
            `;
            return;
        }

        await this.loadSettings(content);
    }

    async loadSettings(container) {
        try {
            const settingsEntities = [
                'bluetooth_switch', 'inverse_mounting', 'aggressive_target_clearing',
                'off_delay', 'aggressive_timeout', 'illuminance_offset',
                'esp32_led', 'status_led'
            ];

            const settings = {};
            for (const entitySuffix of settingsEntities) {
                const entityId = `${this.selectedDevice}_${entitySuffix}`;
                try {
                    const response = await fetch(`/api/entities/${entityId}`);
                    if (response.ok) {
                        settings[entitySuffix] = await response.json();
                    }
                } catch (error) {
                    console.warn(`Could not load ${entityId}:`, error);
                }
            }

            this.renderSettings(container, settings);
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i>
                    Error loading settings: ${error.message}
                </div>
            `;
        }
    }

    renderSettings(container, settings) {
        container.innerHTML = `
            <div class="row g-3">
                ${Object.entries(settings).map(([key, entity]) => `
                    <div class="col-md-6">
                        <div class="card bg-dark">
                            <div class="card-body">
                                <h6 class="card-title">${this.formatEntityName(key)}</h6>
                                ${this.renderSettingControl(key, entity)}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    formatEntityName(entityKey) {
        return entityKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    renderSettingControl(key, entity) {
        if (!entity) {
            return '<p class="text-muted">Entity not available</p>';
        }

        const domain = entity.entity_id.split('.')[0];
        
        switch (domain) {
            case 'switch':
                return `
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" 
                               id="setting_${key}" 
                               ${entity.state === 'on' ? 'checked' : ''}
                               onchange="app.toggleSwitch('${entity.entity_id}', this.checked)">
                        <label class="form-check-label" for="setting_${key}">
                            ${entity.state === 'on' ? 'On' : 'Off'}
                        </label>
                    </div>
                `;
            case 'number':
                return `
                    <div class="input-group">
                        <input type="number" class="form-control" 
                               id="setting_${key}"
                               value="${entity.state}"
                               min="${entity.attributes.min || 0}"
                               max="${entity.attributes.max || 100}"
                               step="${entity.attributes.step || 1}"
                               onchange="app.setNumber('${entity.entity_id}', this.value)">
                        <span class="input-group-text">${entity.attributes.unit_of_measurement || ''}</span>
                    </div>
                `;
            case 'select':
                return `
                    <select class="form-select" id="setting_${key}" 
                            onchange="app.setSelect('${entity.entity_id}', this.value)">
                        ${entity.attributes.options.map(option => `
                            <option value="${option}" ${entity.state === option ? 'selected' : ''}>
                                ${option}
                            </option>
                        `).join('')}
                    </select>
                `;
            default:
                return `<p class="text-muted">Current value: ${entity.state}</p>`;
        }
    }

    async toggleSwitch(entityId, isOn) {
        try {
            const endpoint = isOn ? '/api/services/switch/turn_on' : '/api/services/switch/turn_off';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ entity_id: entityId })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to toggle switch: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error toggling switch:', error);
            this.showError('Failed to update switch');
        }
    }

    async setNumber(entityId, value) {
        try {
            await this.setEntityValue(entityId, parseFloat(value));
        } catch (error) {
            console.error('Error setting number:', error);
            this.showError('Failed to update number value');
        }
    }

    async setSelect(entityId, option) {
        try {
            const response = await fetch('/api/services/select/select_option', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ entity_id: entityId, option })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to set select option: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error setting select option:', error);
            this.showError('Failed to update select option');
        }
    }

    startRealTimeUpdates() {
        // Real-time updates are handled via WebSocket
        this.updateVisualization();
    }

    stopRealTimeUpdates() {
        // WebSocket continues to run, just stops processing updates
    }

    updateVisualization() {
        this.drawVisualization();
    }

    updateConnectionStatus(connected) {
        const status = document.getElementById('connectionStatus');
        const wsStatus = document.getElementById('wsStatus');
        const wsStatusText = document.getElementById('wsStatusText');
        
        if (connected) {
            status.textContent = 'Connected';
            status.className = 'badge bg-success';
            wsStatus.className = 'fas fa-wifi text-success';
            wsStatusText.textContent = 'Connected';
        } else {
            status.textContent = 'Disconnected';
            status.className = 'badge bg-danger';
            wsStatus.className = 'fas fa-wifi text-danger';
            wsStatusText.textContent = 'Disconnected';
        }
    }

    updateLastUpdateTime() {
        const lastUpdate = document.getElementById('lastUpdate');
        lastUpdate.textContent = new Date().toLocaleTimeString();
    }

    showError(message) {
        // Simple toast notification
        console.error(message);
        // Could implement a proper toast notification system here
    }

    showSuccess(message) {
        // Simple success notification
        console.log(message);
        // Could implement a proper toast notification system here
    }

    updateZonePreview() {
        if (!this.selectedZone) return;
        
        const zone = this.selectedZone;
        zone.x1 = parseInt(document.getElementById('zoneX1').value) || zone.x1;
        zone.y1 = parseInt(document.getElementById('zoneY1').value) || zone.y1;
        zone.x2 = parseInt(document.getElementById('zoneX2').value) || zone.x2;
        zone.y2 = parseInt(document.getElementById('zoneY2').value) || zone.y2;
        
        this.drawVisualization();
    }
}

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new Sense360Configurator();
});
