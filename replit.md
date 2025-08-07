# Sense 360 Zone Configurator

## Overview

The Sense 360 Zone Configurator is a Home Assistant add-on that provides a visual interface for configuring detection zones on mmWave presence sensors. The application features a drag-and-drop canvas interface for creating and managing up to 4 detection zones per sensor, real-time target visualization, and seamless integration with Home Assistant's API for device control and monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.
Data integrity: No demo or fake data - application must only work with real Home Assistant integration.

## System Architecture

### Frontend Architecture
- **Single Page Application**: Built with vanilla JavaScript, HTML5, and CSS3
- **Canvas-based Visualization**: HTML5 Canvas for real-time zone drawing and target tracking
- **Bootstrap Framework**: Uses Bootstrap for responsive UI components and styling
- **WebSocket Integration**: Real-time bidirectional communication for live sensor data updates
- **Event-driven Architecture**: Object-oriented JavaScript class structure with event handlers for user interactions

### Backend Architecture
- **Flask Web Framework**: Lightweight Python web server handling HTTP requests and WebSocket connections
- **Flask-Sock**: WebSocket support for real-time communication with the frontend
- **Home Assistant API Integration**: RESTful API client for device discovery, state management, and control
- **Authentication**: Token-based authentication supporting both Supervisor tokens (add-on mode) and manual HA tokens

### Communication Layer
- **REST API Endpoints**: Standard HTTP endpoints for device operations and configuration
- **WebSocket Protocol**: Real-time data streaming for sensor readings and target positions
- **Home Assistant Integration**: Direct API calls to HA core for entity state management and control

### Configuration Management
- **Environment Variables**: Flexible configuration through SUPERVISOR_TOKEN, HA_URL, and HA_TOKEN
- **Zone Persistence**: Client-side zone configuration with backend state synchronization
- **Device Discovery**: Automatic detection of compatible mmWave sensors through HA entity registry

## External Dependencies

### Core Services
- **Home Assistant Core**: Primary integration platform providing device management and API access
- **Home Assistant Supervisor**: Container orchestration and add-on management (when running as add-on)

### Frontend Dependencies
- **Bootstrap 5**: UI framework for responsive design and components
- **Font Awesome 6**: Icon library for user interface elements
- **HTML5 Canvas API**: Native browser API for real-time graphics rendering

### Backend Dependencies
- **Flask**: Python web framework for HTTP server and routing
- **Flask-Sock**: WebSocket support extension for Flask
- **Requests**: HTTP library for Home Assistant API communication
- **Threading**: Python standard library for concurrent WebSocket handling

### Development Tools
- **Docker**: Containerization platform for add-on packaging and deployment
- **Python 3**: Runtime environment for backend services
- **Modern Web Browsers**: Client-side execution environment with Canvas and WebSocket support