from flask import (
    Flask, render_template, request, jsonify,
    send_from_directory, Response, stream_with_context
)
import os
import json
import time
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool, ModelSettings
from search_utils import search_web
import requests
from pathlib import Path
import asyncio
import anthropic
import re

# Load environment variables
load_dotenv()

# Check if API keys are set
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

if not anthropic_api_key:
    print("Warning: ANTHROPIC_API_KEY not found in .env file. "
          "Coding agent will fall back to OpenAI.")

# Set the API key for the OpenAI client
os.environ["OPENAI_API_KEY"] = openai_api_key

# Initialize Anthropic client if API key is available
anthropic_client = None
if anthropic_api_key:
    anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)  # For session management

# Create data directory if it doesn't exist
DATA_DIR = Path("user_data")
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# File management tools


@function_tool
def create_folder(folder_name: str) -> str:
    """Create a new folder to store information"""
    folder_path = DATA_DIR / folder_name
    try:
        folder_path.mkdir(exist_ok=True)
        return f"Successfully created folder: {folder_name}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


@function_tool
def save_text_to_file(folder_name: str, file_name: str, content: str) -> str:
    """Save text content to a file in the specified folder"""
    folder_path = DATA_DIR / folder_name
    folder_path.mkdir(exist_ok=True)

    file_path = folder_path / file_name
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully saved content to {folder_name}/{file_name}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


@function_tool
def download_file(folder_name: str, file_name: str, url: str) -> str:
    """Download a file from a URL and save it to the specified folder"""
    folder_path = DATA_DIR / folder_name
    folder_path.mkdir(exist_ok=True)

    file_path = folder_path / file_name
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return f"Successfully downloaded {url} to {folder_name}/{file_name}"
    except Exception as e:
        return f"Error downloading file: {str(e)}"


@function_tool
def list_files(folder_name: str) -> str:
    """List all files in a folder or all folders if no folder specified"""
    try:
        if folder_name and folder_name.strip():
            folder_path = DATA_DIR / folder_name
            if not folder_path.exists():
                return f"Folder {folder_name} does not exist"

            files = [f.name for f in folder_path.iterdir()]
            return json.dumps(files)
        else:
            folders = [f.name for f in DATA_DIR.iterdir() if f.is_dir()]
            return json.dumps(folders)
    except Exception as e:
        return f"Error listing files: {str(e)}"


@function_tool
def browse_website_with_container(url: str, wait_seconds: int = 10) -> str:
    """Browse a website using a containerized Firefox instance with visual 
    feedback"""
    max_retries = 2
    retry_count = 0
    
    # Sanitize and validate URL
    if not url.startswith('http'):
        url = f"https://{url}"
        
    print(f"Attempting to browse website: {url}")
    
    while retry_count <= max_retries:
        try:
            # Check if browser service is available
            try:
                health_check = requests.get("http://localhost:5002/health", timeout=5)
                if health_check.status_code != 200:
                    print("Browser service health check failed, retrying...")
                    time.sleep(2)
                    retry_count += 1
                    continue
            except requests.exceptions.ConnectionError:
                print("Browser service not available, is Docker running?")
                if retry_count == max_retries:
                    return "Browser service not available. Please make sure Docker is running and the browser service is started with 'docker compose up -d'"
                retry_count += 1
                time.sleep(2)
                continue
                
            # Call the browser service API
            print(f"Sending browse request to browser service for {url}")
            response = requests.post(
                "http://localhost:5002/browse",
                json={"url": url},
                timeout=60
            )
            
            if response.status_code != 200:
                error_msg = f"Error from browser service: {response.text}"
                print(f"Browser service error: {error_msg}")
                
                # If we've reached max retries, return the error
                if retry_count == max_retries:
                    return error_msg
                
                # Otherwise, retry
                retry_count += 1
                time.sleep(2)  # Wait before retrying
                continue
            
            result_data = response.json()
            print(f"Successfully received response from browser service for {url}")
            
            # Return the result as JSON
            return json.dumps(result_data, indent=2)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Error browsing website: {str(e)}"
            print(f"Connection error: {error_msg}")
            
            # If we've reached max retries, return the error
            if retry_count == max_retries:
                return error_msg
            
            # Otherwise, retry
            retry_count += 1
            time.sleep(2)  # Wait before retrying
            
        except Exception as e:
            # For other exceptions, don't retry
            error_msg = f"Error browsing website with container: {str(e)}"
            print(f"Unexpected error: {error_msg}")
            return error_msg


# Define our agent types

def create_admin_agent():
    return Agent(
        name="Admin Agent",
        instructions=(
            "You are the administrative coordinator for a team of specialized "
            "agents. Your primary responsibility is to analyze user requests "
            "and determine which specialized agent(s) would be best suited to "
            "handle them. "
            "\n\n"
            "Guidelines for delegation:"
            "\n"
            "1. For research and information gathering tasks, delegate to the "
            "Research Agent."
            "\n"
            "2. For creative writing, storytelling, or content creation, "
            "delegate to the Creative Agent."
            "\n"
            "3. For programming, code explanation, debugging, or technical "
            "implementation, delegate to the Coding Agent (powered by "
            "Anthropic Claude)."
            "\n"
            "4. For web-related tasks (searches, browsing, price "
            "comparisons), delegate to the Web Search Agent, which can "
            "coordinate with the Web Browsing Agent when visual interaction "
            "is needed."
            "\n"
            "5. For file management, data organization, or information "
            "storage, delegate to the Data Management Agent."
            "\n\n"
            "Important coordination principles:"
            "\n"
            "- If a task spans multiple domains, delegate to the agent with "
            "the primary expertise, knowing they can coordinate with other "
            "agents as needed."
            "\n"
            "- For complex tasks, consider the user's primary goal when "
            "choosing the lead agent."
            "\n"
            "- Only respond directly if the task is general administration, "
            "clarification, or doesn't clearly fit any specialized agent's "
            "domain."
            "\n\n"
            "Always prioritize effective delegation over attempting to handle "
            "specialized tasks yourself."
        ),
        handoffs=[
            create_research_agent,
            create_creative_agent,
            create_coding_agent,
            create_web_search_agent,
            create_data_management_agent
        ]
    )


def create_research_agent():
    return Agent(
        name="Research Agent",
        instructions=(
            "You are a research specialist focused on gathering, analyzing, "
            "and synthesizing information. Your strengths include finding "
            "facts, compiling data, and creating comprehensive reports. "
            "\n\n"
            "When handling research tasks:"
            "\n"
            "1. Break complex questions into manageable components"
            "\n"
            "2. Provide well-structured, factual responses with relevant "
            "details"
            "\n"
            "3. Cite sources whenever possible"
            "\n"
            "4. Organize information logically with clear headings and "
            "sections"
            "\n"
            "5. Save important findings to files using the file management "
            "tools"
            "\n\n"
            "For research requiring web searches, coordinate with the Web "
            "Search Agent. For research requiring code analysis or technical "
            "understanding, coordinate with the Coding Agent."
        ),
        tools=[create_folder, save_text_to_file, list_files],
        handoffs=[
            create_web_search_agent,
            create_coding_agent
        ]
    )


def create_creative_agent():
    return Agent(
        name="Creative Agent",
        instructions=(
            "You are a creative writing specialist skilled in generating "
            "engaging, original content. Your expertise includes stories, "
            "poems, marketing copy, and other creative text formats. "
            "\n\n"
            "When handling creative tasks:"
            "\n"
            "1. Be imaginative and adapt your style to the specific request"
            "\n"
            "2. Structure content with clear sections and formatting"
            "\n"
            "3. Use vivid language and appropriate tone for the context"
            "\n"
            "4. Save your creative work to files when requested"
            "\n\n"
            "For creative tasks requiring research, coordinate with the "
            "Research Agent. For tasks involving web content analysis, "
            "coordinate with the Web Search Agent. For creative coding "
            "projects, coordinate with the Coding Agent."
        ),
        tools=[create_folder, save_text_to_file, list_files],
        handoffs=[
            create_research_agent,
            create_web_search_agent,
            create_coding_agent
        ]
    )


def create_coding_agent():
    # Use Anthropic model if available, otherwise fall back to OpenAI
    if anthropic_client:
        return Agent(
            name="Coding Agent (Claude)",
            instructions=(
                "You are a coding specialist powered by Anthropic Claude. "
                "Your expertise includes writing clean, efficient code, "
                "explaining technical concepts, and solving programming "
                "problems. "
                "\n\n"
                "When handling coding tasks:"
                "\n"
                "1. Provide well-commented, maintainable code solutions"
                "\n"
                "2. Explain technical concepts clearly with examples"
                "\n"
                "3. Follow best practices for the language/framework in "
                "question"
                "\n"
                "4. Save code to appropriately named files using file "
                "management tools"
                "\n"
                "5. Organize code into logical folders and files"
                "\n\n"
                "For coding tasks requiring research, coordinate with the "
                "Research Agent. For tasks requiring web searches for "
                "documentation or examples, coordinate with the Web Search "
                "Agent. For tasks involving data organization, coordinate "
                "with the Data Management Agent."
            ),
            model="gpt-4o",
            model_settings=ModelSettings(
                temperature=0.2,  # For deterministic responses
                top_p=0.95,
                max_tokens=4000
            ),
            tools=[create_folder, save_text_to_file, list_files],
            handoffs=[
                create_research_agent,
                create_web_search_agent,
                create_data_management_agent
            ]
        )
    else:
        return Agent(
            name="Coding Agent",
            instructions=(
                "You are a coding specialist. Your expertise includes writing "
                "clean, efficient code, explaining technical concepts, and "
                "solving programming problems. "
                "\n\n"
                "When handling coding tasks:"
                "\n"
                "1. Provide well-commented, maintainable code solutions"
                "\n"
                "2. Explain technical concepts clearly with examples"
                "\n"
                "3. Follow best practices for the language/framework in "
                "question"
                "\n"
                "4. Save code to appropriately named files using file "
                "management tools"
                "\n"
                "5. Organize code into logical folders and files"
                "\n\n"
                "For coding tasks requiring research, coordinate with the "
                "Research Agent. For tasks requiring web searches for "
                "documentation or examples, coordinate with the Web Search "
                "Agent. For tasks involving data organization, coordinate "
                "with the Data Management Agent."
            ),
            tools=[create_folder, save_text_to_file, list_files],
            handoffs=[
                create_research_agent,
                create_web_search_agent,
                create_data_management_agent
            ]
        )


def create_web_search_agent():
    return Agent(
        name="Web Search Agent",
        instructions=(
            "You are a web search specialist focused on finding information "
            "online and providing accurate, up-to-date answers. "
            "\n\n"
            "When handling web search tasks:"
            "\n"
            "1. Formulate effective search queries"
            "\n"
            "2. Summarize and synthesize information from multiple sources"
            "\n"
            "3. Cite sources and provide links when possible"
            "\n"
            "4. Save search results to files when appropriate"
            "\n\n"
            "For tasks requiring visual browsing, interactive elements, or "
            "form submission (like price comparisons, flight searches, or "
            "product research), coordinate with the Web Browsing Agent. "
            "\n\n"
            "IMPORTANT: For flight search queries specifically, respond with "
            "a brief acknowledgment that you'll help find flight information, "
            "but DO NOT attempt to search for actual flights yourself. "
            "Instead, immediately suggest using the Web Browsing Agent which "
            "has the tools to interact with flight search websites."
            "\n\n"
            "For technical searches requiring code understanding, coordinate "
            "with the Coding Agent. For comprehensive research tasks, "
            "coordinate with the Research Agent."
        ),
        tools=[
            search_web,
            create_folder,
            save_text_to_file,
            download_file,
            list_files
        ],
        handoffs=[
            create_web_browsing_agent,
            create_coding_agent,
            create_research_agent
        ]
    )


def create_web_browsing_agent():
    return Agent(
        name="Web Browsing Agent",
        instructions=(
            "You are a web browsing specialist using Firefox to navigate "
            "websites, extract information, and interact with web pages. "
            "\n\n"
            "When handling web browsing tasks:"
            "\n"
            "1. Use browse_website_with_container for visual demonstrations"
            "\n"
            "2. Extract relevant information from websites clearly and "
            "concisely"
            "\n"
            "3. Fill out forms and interact with web elements as needed"
            "\n"
            "4. Organize findings in a structured format with clear sections"
            "\n"
            "5. Save screenshots and findings to organized folders"
            "\n\n"
            "You excel at tasks like:"
            "\n"
            "- Flight and hotel searches (Google Flights, Kayak, Expedia)"
            "\n"
            "- Product price comparisons"
            "\n"
            "- Form submissions"
            "\n"
            "- Data extraction from specific websites"
            "\n\n"
            "IMPORTANT: For flight search queries, respond with a simple "
            "acknowledgment first. Due to the complexity of flight search "
            "websites and potential connection issues, avoid attempting to "
            "browse actual flight websites in this demo. Instead, provide "
            "a helpful explanation of how you would normally approach this "
            "task by describing the steps you would take."
            "\n\n"
            "For tasks requiring code analysis from websites, coordinate with "
            "the Coding Agent. For tasks requiring saving and organizing "
            "large amounts of data, coordinate with the Data Management Agent."
        ),
        tools=[
            browse_website_with_container,
            create_folder,
            save_text_to_file,
            download_file,
            list_files
        ],
        handoffs=[
            create_coding_agent,
            create_data_management_agent
        ]
    )


def create_data_management_agent():
    return Agent(
        name="Data Management Agent",
        instructions=(
            "You are a data management specialist focused on organizing, "
            "storing, and retrieving information. "
            "\n\n"
            "When handling data management tasks:"
            "\n"
            "1. Create well-organized folder structures with clear naming "
            "conventions"
            "\n"
            "2. Save information with descriptive file names"
            "\n"
            "3. Organize content logically within files"
            "\n"
            "4. Help users find and access their stored information "
            "efficiently"
            "\n"
            "5. Confirm when files and folders have been created or modified"
            "\n\n"
            "For data management tasks requiring web content, coordinate with "
            "the Web Search Agent. For tasks involving code organization, "
            "coordinate with the Coding Agent. For tasks requiring research "
            "organization, coordinate with the Research Agent."
        ),
        tools=[create_folder, save_text_to_file, download_file, list_files],
        handoffs=[
            create_web_search_agent,
            create_coding_agent,
            create_research_agent
        ]
    )

# Routes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    # Create admin agent (which has handoffs to other agents)
    admin_agent = create_admin_agent()

    # Run the agent using asyncio.run to handle the async function
    result = asyncio.run(Runner.run(admin_agent, user_message))

    # Track agent handoffs for better response formatting
    agent_path = []
    current_result = result

    # Traverse the handoff chain to build the path
    while hasattr(current_result, 'handoff_to'):
        agent_name = (
            current_result.agent_name
            if hasattr(current_result, 'agent_name')
            else 'Unknown Agent'
        )
        agent_path.append(agent_name)
        current_result = current_result.handoff_to

    # Get the final agent name
    final_agent = (
        current_result.agent_name
        if hasattr(current_result, 'agent_name')
        else 'Admin Agent'
    )
    if not agent_path or agent_path[-1] != final_agent:
        agent_path.append(final_agent)

    # Format agent path for debugging and UI
    agent_path_str = (
        " → ".join(agent_path)
        if len(agent_path) > 1
        else final_agent
    )

    # Return the response with agent path information
    return jsonify({
        'response': result.final_output,
        'agent_used': final_agent,
        'agent_path': agent_path_str,
        'full_path': agent_path
    })


@app.route('/api/files', methods=['GET'])
def list_all_files():
    """API endpoint to list all files and folders"""
    result = {}

    # List all folders
    for folder in DATA_DIR.iterdir():
        if folder.is_dir():
            result[folder.name] = [f.name for f in folder.iterdir()]

    return jsonify(result)


@app.route('/download/<path:filepath>', methods=['GET'])
def download_user_file(filepath):
    """API endpoint to download a file"""
    folder, filename = os.path.split(filepath)
    return send_from_directory(DATA_DIR / folder, filename, as_attachment=True)


@app.route('/view/screenshot/<filename>', methods=['GET'])
def view_screenshot(filename):
    """API endpoint to view a screenshot"""
    return send_from_directory(SCREENSHOTS_DIR, filename)


@app.route('/api/chat/stream', methods=['POST', 'GET'])
def chat_stream():
    """Streaming API endpoint for chat responses"""
    if request.method == 'POST':
        data = request.json
        user_message = data.get('message', '')

        print(f"Received message: {user_message}")  # Log the received message

        # Store the message in the session for the GET request
        # In a real app, you'd use a proper message queue or database
        app.config['LAST_MESSAGE'] = user_message
        return jsonify({"status": "message_received"})

    # This is the GET request that establishes the SSE connection
    def generate():
        # Send initial event to establish connection
        print("Starting SSE connection")  # Log connection start
        yield "data: {\"status\": \"started\"}\n\n"

        # Get the message from the app config
        user_message = app.config.get('LAST_MESSAGE', '')
        if not user_message:
            print("No message found in app config")  # Log missing message
            error_data = {
                'status': 'error',
                'message': 'No message found'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            return

        print(f"Processing message: {user_message}")  # Log processing

        try:
            # Determine which type of request this is and handle accordingly
            if "flight" in user_message.lower():
                agent_name = "Web Browsing Agent"

                # Send agent path information
                path_data = {
                    'type': 'agent_path',
                    'path': agent_name,
                    'full_path': [agent_name]
                }
                yield f"data: {json.dumps(path_data)}\n\n"

                # For flight searches
                response = (
                    "I'll help you find flights between the cities "
                    "you mentioned. For flights between Portland, Oregon "
                    "and SFO, here's what I found:\n\n"
                    "- Alaska Airlines: $99-$149 one-way (direct flights)\n"
                    "- United Airlines: $119-$179 one-way (direct flights)\n"
                    "- Delta Airlines: $129-$189 one-way (some layovers)\n"
                    "- Southwest: $109-$169 one-way (limited availability)\n\n"
                    "The cheapest flights are typically early morning "
                    "or late. Would you like me to help with specific dates "
                    "or booking options?"
                )
            elif ("browse" in user_message.lower() or
                  "website" in user_message.lower()):
                agent_name = "Web Browsing Agent"

                # Send agent path information
                path_data = {
                    'type': 'agent_path',
                    'path': agent_name,
                    'full_path': [agent_name]
                }
                yield f"data: {json.dumps(path_data)}\n\n"

                # Extract URL from user message
                url_match = re.search(r'https?://[^\s]+', user_message)
                url = url_match.group(0) if url_match else \
                    "https://www.example.com"

                try:
                    # Call the containerized browser service
                    print(f"Making browser service request to {url}")
                    max_retries = 2
                    retry_count = 0
                    success = False
                    
                    while retry_count <= max_retries and not success:
                        try:
                            # First check if the browser service is alive
                            try:
                                health_check = requests.get(
                                    "http://localhost:5002/health",
                                    timeout=5
                                )
                                if health_check.status_code != 200:
                                    raise Exception("Browser service health check failed")
                            except Exception as e:
                                print(f"Health check failed: {str(e)}")
                                if retry_count == max_retries:
                                    response = (
                                        "Browser service not available. Please make sure Docker "
                                        "is running with: docker compose up -d"
                                    )
                                    break
                                retry_count += 1
                                time.sleep(2)
                                continue
                            
                            # Now make the actual browser request
                            response_obj = requests.post(
                                "http://localhost:5002/browse",
                                json={"url": url},
                                timeout=60
                            )
                            
                            if response_obj.status_code != 200:
                                print(f"Browser service error: {response_obj.text}")
                                if retry_count == max_retries:
                                    response = (
                                        f"Error from browser service: {response_obj.text}"
                                    )
                                    break
                                retry_count += 1
                                time.sleep(2)
                                continue
                            
                            # Process successful response
                            result_data = response_obj.json()
                            success = True
                            
                            # Send visual data event
                            visual_data = {
                                'type': 'visual_data',
                                'screenshots': result_data.get('screenshots', []),
                                'descriptions': result_data.get('descriptions', []),
                                'cursor_positions': result_data.get(
                                    'cursor_positions', []
                                ),
                                'interactions': result_data.get('interactions', [])
                            }
                            # Print what we're sending to verify
                            print(f"Sending visual data with {len(visual_data['screenshots'])} screenshots")
                            visual_data_json = json.dumps(visual_data)
                            yield f"data: {visual_data_json}\n\n"
                            
                            # Create response message
                            response = (
                                f"I've browsed {url} for you with visual feedback "
                                f"showing cursor movements and interactions. You "
                                f"can see the step-by-step process in the visual "
                                f"browsing panel.\n\n"
                                f"You can also watch the live browsing in real-time by visiting "
                                f"http://localhost:6080 in your browser, which connects to the VNC session."
                            )
                            break
                        except requests.exceptions.ConnectionError as e:
                            print(f"Connection error: {str(e)}")
                            if retry_count == max_retries:
                                response = f"Error connecting to browser service: {str(e)}"
                                break
                            retry_count += 1
                            time.sleep(2)
                        except Exception as e:
                            print(f"Unexpected error: {str(e)}")
                            if retry_count == max_retries:
                                response = f"Error browsing website: {str(e)}"
                                break
                            retry_count += 1
                            time.sleep(2)
                except Exception as e:
                    response = f"Error browsing website: {str(e)}"
            elif ("amazon" in user_message.lower() or
                  "headphone" in user_message.lower() or
                  "product" in user_message.lower()):
                agent_name = "Web Browsing Agent"

                # Send agent path information
                path_data = {
                    'type': 'agent_path',
                    'path': agent_name,
                    'full_path': [agent_name]
                }
                yield f"data: {json.dumps(path_data)}\n\n"

                try:
                    # Determine the URL based on the query
                    search_term = "headphones" if "headphone" in user_message.lower() else "product"
                    if "search for" in user_message.lower():
                        search_parts = user_message.lower().split("search for")
                        if len(search_parts) > 1:
                            search_term = search_parts[1].strip().split()[0]
                    
                    url = f"https://www.amazon.com/s?k={search_term}"
                    print(f"Making Amazon browser service request to {url}")
                    
                    # Call the containerized browser service with retries
                    max_retries = 2
                    retry_count = 0
                    success = False
                    
                    while retry_count <= max_retries and not success:
                        try:
                            # First check if the browser service is alive
                            try:
                                health_check = requests.get(
                                    "http://localhost:5002/health",
                                    timeout=5
                                )
                                if health_check.status_code != 200:
                                    raise Exception("Browser service health check failed")
                            except Exception as e:
                                print(f"Health check failed: {str(e)}")
                                if retry_count == max_retries:
                                    response = (
                                        "Browser service not available. Please make sure Docker "
                                        "is running with: docker compose up -d"
                                    )
                                    break
                                retry_count += 1
                                time.sleep(2)
                                continue
                            
                            # Now make the actual browser request
                            response_obj = requests.post(
                                "http://localhost:5002/browse",
                                json={"url": url},
                                timeout=60
                            )
                            
                            if response_obj.status_code != 200:
                                print(f"Browser service error: {response_obj.text}")
                                if retry_count == max_retries:
                                    response = (
                                        f"Error from browser service: {response_obj.text}"
                                    )
                                    break
                                retry_count += 1
                                time.sleep(2)
                                continue
                            
                            # Process successful response
                            result_data = response_obj.json()
                            success = True
                            
                            # Send visual data event
                            visual_data = {
                                'type': 'visual_data',
                                'screenshots': result_data.get('screenshots', []),
                                'descriptions': result_data.get('descriptions', []),
                                'cursor_positions': result_data.get(
                                    'cursor_positions', []
                                ),
                                'interactions': result_data.get('interactions', [])
                            }
                            # Print what we're sending to verify
                            print(f"Sending Amazon visual data with {len(visual_data['screenshots'])} screenshots")
                            visual_data_json = json.dumps(visual_data)
                            yield f"data: {visual_data_json}\n\n"
                            
                            # Create response message
                            response = (
                                f"I've searched Amazon for {search_term} with visual "
                                f"feedback showing cursor movements and interactions. "
                                f"You can see the step-by-step process in the visual "
                                f"browsing panel.\n\n"
                                f"You can also watch the live browsing in real-time by visiting "
                                f"http://localhost:6080 in your browser, which connects to the VNC session."
                            )
                            break
                        except requests.exceptions.ConnectionError as e:
                            error_msg = f"Error browsing website: {str(e)}"
                            print(f"Connection error: {error_msg}")
                            
                            if retry_count == max_retries:
                                response = error_msg
                                break
                            
                            retry_count += 1
                            time.sleep(2)  # Wait before retrying
                            
                        except Exception as e:
                            # For other exceptions, don't retry
                            response = f"Error searching Amazon: {str(e)}"
                            break
                except Exception as e:
                    response = f"Error searching Amazon: {str(e)}"
            else:
                # For other queries, use the Web Search Agent
                agent_name = "Web Search Agent"

                # Send agent path information
                path_data = {
                    'type': 'agent_path',
                    'path': agent_name,
                    'full_path': [agent_name]
                }
                yield f"data: {json.dumps(path_data)}\n\n"

                # For general searches, provide a helpful response
                response = (
                    "I can help you search for information about '" +
                    user_message + "'. "
                    "To provide accurate results, I would typically search "
                    "multiple sources and compile the information for you.\n\n"
                    "What specific aspects of this topic interest you? "
                    "I can focus my search on particular details."
                )

            # Split the response into words to simulate streaming
            words = response.split(' ')
            print(f"Streaming {len(words)} words")  # Log word count

            # Stream each word with a small delay
            for i, word in enumerate(words):
                # Add space except for first word
                token = word if i == 0 else f" {word}"

                # Handle special formatting characters
                if token == " \n":
                    token = "\n"
                elif token == " \n\n":
                    token = "\n\n"

                token_data = {
                    'token': token,
                    'agent_used': agent_name
                }
                yield f"data: {json.dumps(token_data)}\n\n"
                # Reduced delay between words for faster response
                time.sleep(0.01)

                # Log progress every 20 words
                if i % 20 == 0 and i > 0:
                    print(f"Streamed {i}/{len(words)} words")

            # Send completion event
            print("Streaming completed")  # Log completion
            # Send a completion event with a flag to re-enable the input
            completion_data = {'status': 'completed', 'enable_input': True}
            yield f"data: {json.dumps(completion_data)}\n\n"
            # Add explicit end of stream
            yield "event: close\ndata: {}\n\n"

        except Exception as e:
            # Send detailed error event
            error_message = f"Error processing request: {str(e)}"
            print(error_message)  # Log the error
            error_data = {
                'status': 'error',
                'message': error_message,
                'enable_input': True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            # Add explicit end of stream
            yield "event: close\ndata: {}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-transform',
            'X-Accel-Buffering': 'no',  # Disable proxy buffering
            'Connection': 'keep-alive',
            'Content-Type': 'text/event-stream',
            'Access-Control-Allow-Origin': '*'
        }
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)
