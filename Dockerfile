ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache \
    python3 \
    python3-dev \
    py3-pip \
    nginx \
    && rm -rf /var/cache/apk/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    flask \
    flask-sock \
    requests \
    websocket-client

WORKDIR /app

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY backend.py /app/backend.py
COPY www/ /app/www/
COPY services/ /etc/services.d/

# Make sure services are executable
RUN chmod +x /etc/services.d/nginx/run
RUN chmod +x /etc/services.d/backend/run

# Create nginx directories
RUN mkdir -p /var/log/nginx /var/run

# Expose port
EXPOSE 8099

# Labels for Home Assistant
LABEL \
    io.hass.name="Sense 360 Zone Configurator" \
    io.hass.description="Helps you to visually create zones for mmWave Presence Sensors with Sense 360 technology" \
    io.hass.arch="armhf|aarch64|i386|amd64|armv7" \
    io.hass.type="addon" \
    io.hass.version="1.2.1"
