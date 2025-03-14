# Agent Workforce Web Interface

A Flask web application that provides a multi-agent workforce with specialized capabilities, including:

- Research Agent
- Creative Agent
- Coding Agent (powered by Anthropic Claude)
- Web Search Agent
- Web Browsing Agent (using Firefox)
- Data Management Agent

## Setup

1. Clone this repository
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables in the `.env` file:
   - Add your OpenAI API key
   - (Optional) Add Google Custom Search API key and Custom Search Engine ID
   - (Optional) Add Bing Search API key

## Usage

1. Start the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://127.0.0.1:5000/`
3. Interact with the agent workforce through the chat interface

## Web Search Configuration

The Web Search Agent can use one of three search methods:

1. **Google Custom Search API** (preferred): Requires a Google API key and Custom Search Engine ID
   - Get these from https://developers.google.com/custom-search/v1/overview
   - Add them to your `.env` file

2. **Bing Search API**: Requires a Bing API key
   - Get this from https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
   - Add it to your `.env` file

3. **Mock Search**: Used as a fallback if no API keys are provided
   - Returns simulated search results for demonstration purposes

## Project Structure

- `app.py`: Main Flask application
- `search_utils.py`: Utility functions for web search
- `templates/index.html`: Web interface template
- `.env`: Environment variables
- `requirements.txt`: Python dependencies

## Extending the Application

To add more agent types:

1. Create a new agent creation function in `app.py`
2. Add the new agent to the handoffs list in the `create_admin_agent` function
3. Update the instructions in the Admin Agent to include the new agent type
4. Update the HTML template to list the new agent type

## License

MIT

# Browser Automation with Flask and Selenium

This project provides a web-based interface for browser automation using Flask and Selenium.

## Features

- Browser automation with Selenium
- Visual feedback with screenshots
- Docker-based browser service for stability
- Real-time visual browsing with VNC

## Visual Browser Automation

This project now includes a visual browser automation feature that allows you to watch the browser in real-time as it performs automated tasks.

### How to Use Visual Browsing

1. Start the Docker container:
   ```
   docker compose up -d
   ```

2. Access the visual browser interface:
   - **VNC Client**: Connect to localhost:5900 (password: 123456)

3. Use the browser automation features through the Flask app or directly via the API:
   ```
   curl -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com"}' http://localhost:5002/browse
   ```

4. Watch as the browser performs the automated tasks with a visible red cursor

For more details, see [README_VISUAL_BROWSING.md](README_VISUAL_BROWSING.md).