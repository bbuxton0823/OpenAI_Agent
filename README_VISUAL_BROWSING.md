# Visual Browser Automation

This project provides a Docker-based browser automation service with visual feedback. You can watch the browser in real-time as it performs automated tasks.

## Features

- Firefox browser running in a Docker container
- Real-time visual feedback through VNC
- Web-based access via noVNC (no password required)
- Red cursor visualization for tracking mouse movements
- API for browser automation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Web browser

### Setup and Running

1. Build and start the container:
   ```
   docker compose up -d
   ```

2. Access the visual browser interface:
   - **Web Interface (noVNC)**: Open http://localhost:6080 in your browser
   - **VNC Client**: Connect to localhost:5900 (no password required)

3. Use the API to control the browser:
   - The API is available at http://localhost:5002
   - Example: `curl -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com"}' http://localhost:5002/browse`

## Watching Browser Automation

1. Start a browser automation task through the API
2. Open the noVNC interface at http://localhost:6080
3. Watch as the browser performs the automated tasks with a visible red cursor

## Integration with Flask App

The main Flask application communicates with this browser service to perform web automation tasks. When you request browser automation through the main app, you can watch the process in real-time through the noVNC interface.

## Troubleshooting

- If the VNC connection fails, ensure ports 5900 and 6080 are not being used by other applications
- If the browser is not visible, try restarting the container: `docker compose restart`
- Check container logs for errors: `docker compose logs browser-service` 