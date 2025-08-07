# Sense 360 Zone Configurator

A Home Assistant add-on to visually create zones for mmWave Presence Sensors with Sense 360 technology.

## Features

- **Visual Zone Configuration**: Drag-and-drop interface for creating detection zones
- **Real-time Updates**: Live WebSocket connection showing sensor data and target tracking
- **Multiple Zone Support**: Configure up to 4 detection zones per sensor
- **Settings Management**: Adjust sensor parameters through an intuitive UI
- **Target Visualization**: See live targets detected by the mmWave sensor
- **Home Assistant Integration**: Seamless integration with Home Assistant's API

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Sense 360 Zone Configurator" add-on
3. Start the add-on
4. Access the interface through the Home Assistant sidebar

## Usage

### Getting Started

1. **Select a Sensor**: Choose your mmWave sensor from the dropdown menu
2. **Create Zones**: Click and drag on the canvas to create detection zones
3. **Configure Properties**: Select zones to adjust their settings and coordinates
4. **Monitor Targets**: View real-time target detection in the visualization

### Zone Management

- **Create Zone**: Drag on the canvas or use the "Add Zone" button
- **Select Zone**: Click on any zone to view and edit its properties
- **Modify Zone**: Adjust coordinates and settings in the control panel
- **Delete Zone**: Select a zone and click the delete button

### Settings

Access the settings menu to configure:
- Bluetooth functionality
- LED indicators
- Detection sensitivity
- Installation parameters
- Off delays and timeouts

## Technical Details

### Architecture

- **Backend**: Flask application with WebSocket support
- **Frontend**: Vanilla JavaScript with HTML5 Canvas
- **Proxy**: Nginx reverse proxy for performance
- **Integration**: Direct Home Assistant API communication

### Supported Entities

The configurator works with mmWave sensors that provide these entity types:
- Zone coordinates (begin_x, begin_y, end_x, end_y)
- Target tracking (target_x, target_y, target_active)
- Configuration settings (max_distance, installation_angle)
- Control switches and delays

### Real-time Updates

The application uses WebSocket connections to provide:
- Live target position updates
- Real-time zone occupancy status
- Instant configuration changes
- Connection status monitoring

## Configuration

### Add-on Configuration

```yaml
name: "Sense 360 Zone Configurator"
description: "Visual zone configuration for mmWave sensors"
version: "1.2.1"
slug: "sense-360-zone-configurator"
ingress: true
homeassistant_api: true
