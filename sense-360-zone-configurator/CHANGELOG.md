# Changelog

All notable changes to this project will be documented in this file.

## [1.2.1] - 2025-08-07

### Added
- Initial release of Sense 360 Zone Configurator
- Visual interface for configuring detection zones on mmWave presence sensors
- Support for up to 4 detection zones per sensor
- Real-time target visualization
- Home Assistant API integration
- WebSocket support for live updates
- Bootstrap-based responsive UI
- Complete Docker containerization

### Features
- Drag-and-drop zone configuration
- Real-time sensor data display
- Seamless Home Assistant integration
- Production-ready deployment with Docker
- No demo data - requires real Home Assistant credentials

### Technical
- Flask backend with WebSocket support
- HTML5 Canvas for zone visualization
- Nginx reverse proxy configuration
- Multi-platform Docker builds (amd64, arm64, armv7)