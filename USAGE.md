# Agent Workforce with Visual Browser Capability

This guide explains how to set up and use the Agent Workforce application with its visual browser capability.

## Setup

1. **Start the Browser Service**
   ```bash
   docker compose up -d
   ```
   This launches a Docker container with Firefox, VNC server, and the browser service API.

2. **Start the Main Application**
   ```bash
   python app.py
   ```
   This starts the Flask application on port 5001.

3. **Access the Web Interface**
   Open your browser and go to:
   ```
   http://localhost:5001
   ```

4. **Access Visual Browsing (Optional)**
   To see live browsing in real-time, open:
   ```
   http://localhost:6080
   ```
   This connects directly to the VNC server running in the Docker container.

## Using the Application

The application provides several specialized agents:
- **Admin Agent**: Coordinates between specialized agents
- **Research Agent**: Gathers and analyzes information
- **Creative Agent**: Handles creative writing tasks
- **Coding Agent**: Helps with programming tasks (powered by Claude or GPT-4)
- **Web Search Agent**: Performs web searches
- **Web Browsing Agent**: Automates and visualizes web browsing
- **Data Management Agent**: Organizes information and files

### Visual Browsing

To use the visual browsing capability:

1. **Ask for website browsing**
   Example prompts:
   - "Browse example.com for me"
   - "Show me amazon search results for headphones"
   - "Visit wikipedia.org and show me what you see"

2. **View the Results**
   The application will show:
   - Visual feedback in the right panel with screenshots
   - Cursor movements and interactions
   - Step-by-step navigation through the browsing session

3. **Live Browsing**
   For real-time viewing, open the VNC interface at `http://localhost:6080` while browsing is happening.

### Troubleshooting

- If the browser service isn't responding, make sure Docker is running and the container is started.
- If screenshots aren't appearing, check the browser service logs with `docker compose logs`.
- For connectivity issues, restart the Docker container with `docker compose restart`.

## Technical Information

- The browser container runs on ports 5002 (API), 5900 (VNC), and 6080 (noVNC web interface).
- The main application runs on port 5001.
- Screenshots are stored in the user_data/screenshots directory.
- The browser sessions are non-headless, allowing real-time viewing via VNC.