/**
 * Agent Workforce - Main JavaScript
 * Handles streaming responses and visual browsing
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatContainer = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const fileExplorer = document.getElementById('file-list');
    const refreshFilesBtn = document.getElementById('refresh-files-btn') || document.createElement('button'); // Create if not exists
    const screenshotCard = document.getElementById('screenshot-card') || document.createElement('div');
    const screenshotPreview = document.getElementById('screenshot-preview') || document.createElement('img');
    const themeToggle = document.getElementById('themeToggle');
    const streamingToggle = document.getElementById('streamingToggle');
    
    // Visual browsing elements
    const visualBrowsingCard = document.getElementById('visual-browsing-card') || document.createElement('div');
    const visualPreview = document.getElementById('current-screenshot') || document.createElement('img');
    const visualDescription = document.getElementById('visual-description') || document.createElement('div');
    const visualCurrentStep = document.getElementById('current-step') || document.createElement('span');
    const visualTotalSteps = document.getElementById('total-steps') || document.createElement('span');
    const prevVisualBtn = document.getElementById('prev-step') || document.createElement('button');
    const nextVisualBtn = document.getElementById('next-step') || document.createElement('button');
    const playVisualBtn = document.getElementById('play-visual') || document.createElement('button');
    const cursorIndicator = document.createElement('div'); // Create cursor element
    cursorIndicator.className = 'cursor-indicator';
    
    // Visual browsing state
    let visualScreenshots = [];
    let visualDescriptions = [];
    let visualCursorPositions = [];
    let currentVisualIndex = 0;
    let visualPlayInterval = null;
    let visualInteractions = [];
    
    // Global variables for visual monitoring
    let visualData = null;
    let currentVisualStep = 0;
    
    // Theme toggle functionality
    themeToggle.addEventListener('click', function() {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-bs-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        html.setAttribute('data-bs-theme', newTheme);
        
        // Update toggle button
        if (newTheme === 'dark') {
            themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i> <span>Light Mode</span>';
        } else {
            themeToggle.innerHTML = '<i class="bi bi-moon-fill"></i> <span>Dark Mode</span>';
        }
        
        // Save preference to localStorage
        localStorage.setItem('theme', newTheme);
    });
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        if (savedTheme === 'dark') {
            themeToggle.innerHTML = '<i class="bi bi-sun-fill"></i> <span>Light Mode</span>';
        }
    }
    
    // Function to add a message to the chat
    function addMessage(content, isUser, agentName = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'agent-message';
        
        if (!isUser && agentName) {
            const agentTag = document.createElement('div');
            agentTag.className = 'agent-tag';
            agentTag.textContent = agentName;
            messageDiv.appendChild(agentTag);
        }
        
        // For agent messages, create a content div that can be updated during streaming
        if (!isUser) {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Process the content for better formatting
            let formattedContent = processMessageContent(content);
            
            contentDiv.innerHTML = formattedContent;
            messageDiv.appendChild(contentDiv);
        } else {
            messageDiv.innerHTML += content;
        }
        
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to process message content for better formatting
    function processMessageContent(content) {
        // Replace numbered lists with better formatting
        content = content.replace(/(\d+\.\s+)(\*\*[^*]+\*\*:?)/g, '<div class="list-item"><span class="list-number">$1</span><span class="list-title">$2</span>');
        
        // Add proper spacing after list titles
        content = content.replace(/(<\/span><\/div>)([^<])/g, '$1<div class="list-content">$2');
        
        // Close list content divs before new list items
        content = content.replace(/([^>])(<div class="list-item">)/g, '$1</div>$2');
        
        // Close the last list content div if it exists
        if (content.includes('<div class="list-content">') && !content.endsWith('</div>')) {
            content += '</div>';
        }
        
        // Format headers
        content = content.replace(/\*\*([^*:]+)\*\*/g, '<h4 class="content-header">$1</h4>');
        
        // Format bold text that isn't a header
        content = content.replace(/\*\*([^*]+:[^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Format bullet points
        content = content.replace(/- ([^<]+)/g, '<div class="bullet-point">• $1</div>');
        
        return content;
    }
    
    // Function to show a screenshot
    function showScreenshot(filename) {
        screenshotPreview.src = `/view/screenshot/${filename}`;
        screenshotCard.style.display = 'block';
        screenshotPreview.onload = function() {
            window.scrollTo(0, document.body.scrollHeight);
        };
    }
    
    // Function to show visual browsing
    function showVisualBrowsing(screenshots, descriptions, cursorPositions) {
        if (!screenshots || screenshots.length === 0) return;
        
        // Hide screenshot card if it's visible
        screenshotCard.style.display = 'none';
        
        // Set up visual browsing state
        visualScreenshots = screenshots;
        visualDescriptions = descriptions || Array(screenshots.length).fill('');
        visualCursorPositions = cursorPositions || Array(screenshots.length).fill(null);
        currentVisualIndex = 0;
        
        // Update UI
        updateVisualDisplay();
        
        // Show the card
        visualBrowsingCard.style.display = 'block';
        
        // Scroll to the card
        window.scrollTo(0, document.body.scrollHeight);
    }
    
    // Enhanced visual display functions
    function updateVisualDisplay() {
        // Update progress
        visualCurrentStep.textContent = (currentVisualIndex + 1).toString();
        visualTotalSteps.textContent = visualScreenshots.length.toString();
        
        // Get current interaction type
        const interactionType = visualInteractions ? 
            (visualInteractions[currentVisualIndex] || 'none') : 'none';
        
        // Update image
        const screenshotPath = visualScreenshots[currentVisualIndex];
        visualPreview.src = `/${screenshotPath}`;
        
        // Update description
        visualDescription.textContent = visualDescriptions[currentVisualIndex] || '';
        
        // Update cursor position
        const cursorPos = visualCursorPositions ? 
            visualCursorPositions[currentVisualIndex] : null;
        
        // Reset cursor animation classes
        if (cursorIndicator) {
            cursorIndicator.classList.remove(
                'cursor-moving', 
                'cursor-typing', 
                'cursor-clicking',
                'cursor-hovering'
            );
        }
        
        if (cursorPos) {
            // Show cursor with proper animation
            cursorIndicator.style.display = 'block';
            
            // Position cursor based on provided coordinates
            visualPreview.onload = function() {
                const rect = visualPreview.getBoundingClientRect();
                const imgWidth = visualPreview.naturalWidth || 1280;
                const imgHeight = visualPreview.naturalHeight || 800;
                const displayWidth = visualPreview.width;
                const displayHeight = visualPreview.height;
                
                // Calculate position relative to displayed image size
                const x = (cursorPos.x / imgWidth) * displayWidth;
                const y = (cursorPos.y / imgHeight) * displayHeight;
                
                // Apply position
                cursorIndicator.style.left = `${x}px`;
                cursorIndicator.style.top = `${y}px`;
                
                // Add animation class based on interaction type
                if (interactionType && interactionType.includes('typing')) {
                    cursorIndicator.classList.add('cursor-typing');
                } else if (interactionType && interactionType.includes('click')) {
                    cursorIndicator.classList.add('cursor-clicking');
                } else if (interactionType && interactionType.includes('hover')) {
                    cursorIndicator.classList.add('cursor-hovering');
                } else {
                    cursorIndicator.classList.add('cursor-moving');
                }
            };
        } else if (cursorIndicator) {
            cursorIndicator.style.display = 'none';
        }
    }
    
    // Visual browsing navigation
    prevVisualBtn.addEventListener('click', function() {
        if (currentVisualIndex > 0) {
            currentVisualIndex--;
            updateVisualDisplay();
        }
    });
    
    nextVisualBtn.addEventListener('click', function() {
        if (currentVisualIndex < visualScreenshots.length - 1) {
            currentVisualIndex++;
            updateVisualDisplay();
        }
    });
    
    // Play/pause visual browsing
    playVisualBtn.addEventListener('click', function() {
        if (visualPlayInterval) {
            // Stop playback
            clearInterval(visualPlayInterval);
            visualPlayInterval = null;
            playVisualBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        } else {
            // Start playback
            playVisualBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
            visualPlayInterval = setInterval(function() {
                if (currentVisualIndex < visualScreenshots.length - 1) {
                    currentVisualIndex++;
                    updateVisualDisplay();
                } else {
                    // Stop at the end
                    clearInterval(visualPlayInterval);
                    visualPlayInterval = null;
                    playVisualBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
                }
            }, 2000); // Change slide every 2 seconds
        }
    });
    
    // Function to handle streaming messages
    async function sendMessageStreaming() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        userInput.value = '';
        
        // Create a new message div for the agent response
        const messageDiv = addMessage('', false, 'System');
        const contentDiv = messageDiv.querySelector('.message-content');
        
        // Add typing indicator
        const typingIndicator = document.createElement('span');
        typingIndicator.className = 'typing-indicator';
        contentDiv.appendChild(typingIndicator);
        
        // Mark as streaming
        messageDiv.classList.add('streaming-active');
        
        // Disable input while streaming
        userInput.disabled = true;
        sendButton.disabled = true;
        
        try {
            // First, send the message to the server
            const postResponse = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            if (!postResponse.ok) {
                throw new Error('Failed to send message');
            }
            
            // Then establish SSE connection
            const timestamp = new Date().getTime();
            const eventSource = new EventSource(`/api/chat/stream?t=${timestamp}`);
            
            let responseText = '';
            let agentUsed = 'System';
            let agentPath = null;
            let retryCount = 0;
            const maxRetries = 3;
            let intentionallyClosed = false;
            
            // Listen for the close event
            eventSource.addEventListener('close', function(event) {
                console.log('Server requested connection close');
                intentionallyClosed = true;
                eventSource.close();
                
                // Re-enable input if it's still disabled
                if (userInput.disabled) {
                    userInput.disabled = false;
                    sendButton.disabled = false;
                    userInput.focus();
                }
            });
            
            eventSource.onmessage = function(event) {
                // Reset retry count on successful message
                retryCount = 0;
                
                const data = JSON.parse(event.data);
                
                // Handle different types of events
                if (data.status === 'started') {
                    console.log('Streaming started');
                } 
                else if (data.type === 'agent_path') {
                    // Update agent path
                    agentPath = data.path;
                    const agentTag = messageDiv.querySelector('.agent-tag');
                    if (agentTag) {
                        // Create path display
                        const pathDisplay = document.createElement('div');
                        pathDisplay.className = 'agent-path';
                        pathDisplay.textContent = agentPath;
                        
                        // Replace agent tag with path display
                        agentTag.innerHTML = agentPath.split(' → ').pop(); // Show final agent
                        agentTag.appendChild(pathDisplay);
                    }
                }
                else if (data.token) {
                    // Append token to response
                    responseText += data.token;
                    
                    // Update agent name if provided
                    if (data.agent_used) {
                        agentUsed = data.agent_used;
                        const agentTag = messageDiv.querySelector('.agent-tag');
                        if (agentTag && !agentPath) {
                            agentTag.textContent = agentUsed;
                        }
                    }
                    
                    // Update content
                    contentDiv.innerHTML = processMessageContent(responseText);
                    
                    // Scroll to bottom
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                else if (data.status === 'completed') {
                    // Remove typing indicator and streaming class
                    if (typingIndicator.parentNode) {
                        typingIndicator.parentNode.removeChild(typingIndicator);
                    }
                    messageDiv.classList.remove('streaming-active');
                    
                    // Process any visual browsing data in the response
                    const hasVisualData = processVisualBrowsingData(responseText);
                    
                    // If no visual browsing data was found, hide the VNC viewer
                    if (!hasVisualData && !responseText.includes('browse') && !responseText.includes('website')) {
                        hideVncViewer();
                    }
                    
                    // Mark as intentionally closed to prevent auto-reconnect
                    intentionallyClosed = true;
                    
                    // Close the connection
                    eventSource.close();
                    
                    // Check for enable_input flag (default to true if not specified)
                    if (data.enable_input !== false) {
                        // Re-enable input
                        userInput.disabled = false;
                        sendButton.disabled = false;
                        userInput.focus();
                    }
                }
                else if (data.status === 'error') {
                    // Display error
                    contentDiv.innerHTML = `<div class="error-message">${data.message}</div>`;
                    
                    // Remove typing indicator and streaming class
                    if (typingIndicator.parentNode) {
                        typingIndicator.parentNode.removeChild(typingIndicator);
                    }
                    messageDiv.classList.remove('streaming-active');
                    
                    // Mark as intentionally closed to prevent auto-reconnect
                    intentionallyClosed = true;
                    
                    // Close the connection
                    eventSource.close();
                    
                    // Check for enable_input flag (default to true if not specified)
                    if (data.enable_input !== false) {
                        // Re-enable input
                        userInput.disabled = false;
                        sendButton.disabled = false;
                        userInput.focus();
                    }
                }
            };
            
            eventSource.onerror = function(error) {
                console.error('EventSource error:', error);
                
                // If we intentionally closed the connection, don't retry
                if (intentionallyClosed) {
                    console.log('Connection was intentionally closed, not retrying');
                    return;
                }
                
                // Implement retry logic
                retryCount++;
                
                if (retryCount <= maxRetries) {
                    console.log(`Retrying connection (${retryCount}/${maxRetries})...`);
                    
                    // Update message to show retry attempt
                    contentDiv.innerHTML = `<div class="info-message">Connection issue. Retrying (${retryCount}/${maxRetries})...</div>`;
                    
                    // The EventSource will automatically try to reconnect
                    return;
                }
                
                // If we've exceeded max retries, show error and give up
                contentDiv.innerHTML = '<div class="error-message">Connection error. Please try again.</div>';
                
                // Remove typing indicator and streaming class
                if (typingIndicator.parentNode) {
                    typingIndicator.parentNode.removeChild(typingIndicator);
                }
                messageDiv.classList.remove('streaming-active');
                
                // Mark as intentionally closed to prevent auto-reconnect
                intentionallyClosed = true;
                
                // Close the connection
                eventSource.close();
                
                // Re-enable input
                userInput.disabled = false;
                sendButton.disabled = false;
                userInput.focus();
            };
            
        } catch (error) {
            console.error('Error in streaming:', error);
            
            // Display error in the message
            contentDiv.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            
            // Remove typing indicator and streaming class
            if (typingIndicator.parentNode) {
                typingIndicator.parentNode.removeChild(typingIndicator);
            }
            messageDiv.classList.remove('streaming-active');
            
            // Re-enable input
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    }
    
    // Function to load files
    async function loadFiles() {
        console.log('Loading files...');
        try {
            // Add cache-busting parameter to prevent caching
            const timestamp = new Date().getTime();
            const response = await fetch(`/api/files?_=${timestamp}`);
            const data = await response.json();
            
            console.log('Files loaded:', data);
            
            // Clear file explorer
            fileExplorer.innerHTML = '';
            
            if (!data || Object.keys(data).length === 0) {
                console.log('No files found in response');
                fileExplorer.innerHTML = '<div class="text-center"><p>No files yet. Ask an agent to create some!</p></div>';
                return;
            }
            
            // Create file explorer content
            let fileCount = 0;
            for (const [folder, files] of Object.entries(data)) {
                console.log(`Processing folder: ${folder} with ${files.length} files`);
                
                const folderDiv = document.createElement('div');
                folderDiv.className = 'folder-item';
                folderDiv.innerHTML = `<i class="bi bi-folder"></i> <strong>${folder}</strong>`;
                fileExplorer.appendChild(folderDiv);
                
                // Create file items
                for (const file of files) {
                    fileCount++;
                    const fileDiv = document.createElement('div');
                    fileDiv.className = 'file-item';
                    
                    // Check if it's a screenshot
                    if (file.match(/screenshot_\d+\.png/) || file.match(/step_.*\.png/)) {
                        fileDiv.innerHTML = `<a href="#" class="file-link screenshot-link" data-filename="${file}"><i class="bi bi-file-image"></i> ${file}</a>`;
                        
                        // Add event listener for screenshot preview
                        fileDiv.querySelector('.screenshot-link').addEventListener('click', function(e) {
                            e.preventDefault();
                            const filename = this.getAttribute('data-filename');
                            showScreenshot(filename);
                        });
                    } else {
                        fileDiv.innerHTML = `<a href="/download/${folder}/${file}" class="file-link" download><i class="bi bi-file-text"></i> ${file}</a>`;
                    }
                    
                    fileExplorer.appendChild(fileDiv);
                }
            }
            
            console.log(`Total files displayed: ${fileCount}`);
            
            if (fileCount === 0) {
                fileExplorer.innerHTML = '<div class="text-center"><p>No files found in the folders. Ask an agent to create some!</p></div>';
            }
        } catch (error) {
            console.error('Error loading files:', error);
            fileExplorer.innerHTML = '<div class="text-center"><p>Error loading files. Please try again.</p></div>';
        }
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessageStreaming);
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessageStreaming();
        }
    });
    
    // Enhanced refresh button with visual feedback
    refreshFilesBtn.addEventListener('click', function() {
        // Add refreshing class for animation
        refreshFilesBtn.classList.add('refreshing');
        // Disable button during refresh
        refreshFilesBtn.disabled = true;
        
        // Load files
        loadFiles().finally(() => {
            // Remove refreshing class and re-enable button after a short delay
            setTimeout(() => {
                refreshFilesBtn.classList.remove('refreshing');
                refreshFilesBtn.disabled = false;
            }, 500);
        });
    });
    
    // Initial load of files
    loadFiles();

    // Function to show the VNC viewer iframe
    function showVncViewer() {
        const vncContainer = document.getElementById('vnc-container');
        const vncIframe = document.getElementById('vnc-iframe');
        const toggleBtn = document.getElementById('toggle-vnc-btn');
        
        if (vncContainer && vncIframe) {
            // Set the iframe source to the VNC viewer URL
            // Use the same origin as the current page to avoid cross-origin issues
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            const port = window.location.port;
            vncIframe.src = `${protocol}//${hostname}:${port}/vnc`;
            
            // Show the container
            vncContainer.style.display = 'block';
            
            // Update toggle button text
            if (toggleBtn) {
                toggleBtn.textContent = 'Hide Viewer';
            }
            
            console.log('VNC viewer displayed');
        } else {
            console.error('VNC container or iframe not found');
        }
    }
    
    // Automatically show VNC viewer when visual content is displayed
    document.addEventListener('DOMContentLoaded', function() {
        // Add event listener for visual content display
        const visualContent = document.getElementById('visual-content');
        const visualPlaceholder = document.getElementById('visual-placeholder');
        
        // Create a MutationObserver to watch for style changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style' && 
                    visualContent.style.display === 'block' && 
                    visualPlaceholder.style.display === 'none') {
                    // Visual content is now displayed, show VNC viewer
                    showVncViewer();
                }
            });
        });
        
        // Start observing
        if (visualContent) {
            observer.observe(visualContent, { attributes: true });
        }
    });
    
    // Function to hide the VNC viewer iframe
    function hideVncViewer() {
        const vncContainer = document.getElementById('vnc-container');
        const vncIframe = document.getElementById('vnc-iframe');
        const toggleBtn = document.getElementById('toggle-vnc-btn');
        
        if (vncContainer && vncIframe) {
            // Clear the iframe source
            vncIframe.src = '';
            
            // Hide the container
            vncContainer.style.display = 'none';
            
            // Update toggle button text
            if (toggleBtn) {
                toggleBtn.textContent = 'Show Viewer';
            }
            
            console.log('VNC viewer hidden');
        }
    }
    
    // Toggle VNC viewer visibility
    function toggleVncViewer() {
        const vncContainer = document.getElementById('vnc-container');
        
        if (vncContainer) {
            if (vncContainer.style.display === 'none') {
                showVncViewer();
            } else {
                hideVncViewer();
            }
        }
    }
    
    // Function to process visual browsing data from the response
    function processVisualBrowsingData(responseText) {
        try {
            // First, try to find JSON data enclosed in code blocks
            let jsonMatch = responseText.match(/```(?:json)?\n([\s\S]*?)\n```/);
            
            // If not found, try to find JSON data without code blocks
            if (!jsonMatch) {
                // Look for JSON objects that might contain visual browsing data
                jsonMatch = responseText.match(/(\{[\s\S]*?"screenshots"[\s\S]*?\})/);
            }
            
            if (!jsonMatch) return;
            
            const jsonData = jsonMatch[1].trim();
            if (!jsonData) return;
            
            // Parse the JSON data
            const data = JSON.parse(jsonData);
            
            // Check if this is visual browsing data
            if (data.screenshots && data.screenshots.length > 0) {
                console.log('Visual browsing data found:', data);
                
                // Make sure we have all required properties
                if (!data.descriptions) {
                    data.descriptions = Array(data.screenshots.length).fill('');
                }
                
                if (!data.cursor_positions) {
                    data.cursor_positions = Array(data.screenshots.length).fill(null);
                }
                
                if (!data.interactions) {
                    data.interactions = Array(data.screenshots.length).fill('none');
                }
                
                initializeVisualBrowsing(data);
                
                // Show the VNC viewer
                showVncViewer();
                
                return true;
            }
        } catch (error) {
            console.error('Error processing visual browsing data:', error);
        }
        return false;
    }

    // Initialize visual browsing UI with enhanced controls
    function initializeVisualBrowsing(data) {
        // Add styles first
        addVisualStyles();
        
        // Parse the data
        const result = typeof data === 'string' ? JSON.parse(data) : data;
        
        // Store the data globally
        visualScreenshots = result.screenshots || [];
        visualDescriptions = result.descriptions || [];
        visualCursorPositions = result.cursor_positions || [];
        visualInteractions = result.interactions || [];
        currentVisualIndex = 0;
        
        // Create or update the visual browsing UI
        if (!document.getElementById('visual-browsing-container')) {
            // Create container
            const container = document.createElement('div');
            container.id = 'visual-browsing-container';
            container.className = 'visual-browsing';
            
            // Create title
            const title = document.createElement('h3');
            title.textContent = `Visual Browsing: ${result.title || result.url}`;
            
            // Create visual container
            const visualContainer = document.createElement('div');
            visualContainer.className = 'visual-container';
            
            // Create image preview
            const preview = document.createElement('img');
            preview.className = 'visual-preview';
            preview.id = 'visual-preview';
            
            // Create cursor indicator
            const cursor = document.createElement('div');
            cursor.className = 'cursor-indicator';
            cursor.id = 'cursor-indicator';
            
            // Add preview and cursor to container
            visualContainer.appendChild(preview);
            visualContainer.appendChild(cursor);
            
            // Create description
            const description = document.createElement('div');
            description.className = 'visual-description';
            description.id = 'visual-description';
            
            // Create controls
            const controls = document.createElement('div');
            controls.className = 'visual-controls';
            controls.style.display = 'flex';
            controls.style.justifyContent = 'space-between';
            controls.style.marginTop = '10px';
            
            // Create progress indicator
            const progress = document.createElement('div');
            progress.className = 'visual-progress';
            progress.innerHTML = 'Step <span id="visual-current-step">1</span> of <span id="visual-total-steps">0</span>';
            
            // Create buttons
            const buttons = document.createElement('div');
            buttons.className = 'visual-buttons';
            
            const prevButton = document.createElement('button');
            prevButton.textContent = '← Previous';
            prevButton.style.marginRight = '5px';
            prevButton.onclick = function() {
                if (currentVisualIndex > 0) {
                    currentVisualIndex--;
                    updateVisualDisplay();
                }
            };
            
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Next →';
            nextButton.onclick = function() {
                if (currentVisualIndex < visualScreenshots.length - 1) {
                    currentVisualIndex++;
                    updateVisualDisplay();
                }
            };
            
            // Add buttons to controls
            buttons.appendChild(prevButton);
            buttons.appendChild(nextButton);
            
            // Add progress and buttons to controls
            controls.appendChild(progress);
            controls.appendChild(buttons);
            
            // Add all elements to container
            container.appendChild(title);
            container.appendChild(visualContainer);
            container.appendChild(description);
            container.appendChild(controls);
            
            // Add container to chat
            const chatMessages = document.querySelector('.chat-messages');
            chatMessages.appendChild(container);
            
            // Store references to elements
            visualPreview = preview;
            visualDescription = description;
            visualCurrentStep = document.getElementById('visual-current-step');
            visualTotalSteps = document.getElementById('visual-total-steps');
            cursorIndicator = cursor;
        }
        
        // Update the display
        updateVisualDisplay();
        
        // Scroll to the visual browsing container
        document.getElementById('visual-browsing-container').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    // Add CSS for cursor animations
    function addVisualStyles() {
        if (document.getElementById('visual-browsing-styles')) {
            return; // Styles already added
        }
        
        const styleElement = document.createElement('style');
        styleElement.id = 'visual-browsing-styles';
        styleElement.textContent = `
            .cursor-indicator {
                width: 20px;
                height: 20px;
                background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20"><path d="M5,2 L18,15 L15,18 L2,5 L5,2 Z" fill="white" stroke="black" stroke-width="1"/></svg>');
                background-size: contain;
                background-repeat: no-repeat;
                position: absolute;
                pointer-events: none;
                z-index: 1000;
                transition: left 0.3s, top 0.3s;
            }
            
            .cursor-moving {
                animation: cursorPulse 1.5s infinite;
            }
            
            .cursor-typing {
                animation: cursorTyping 0.5s infinite;
            }
            
            .cursor-clicking {
                animation: cursorClick 0.5s;
            }
            
            .cursor-hovering {
                animation: cursorHover 2s infinite;
            }
            
            @keyframes cursorPulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
            
            @keyframes cursorTyping {
                0% { transform: translateY(0); }
                50% { transform: translateY(2px); }
                100% { transform: translateY(0); }
            }
            
            @keyframes cursorClick {
                0% { transform: scale(1); }
                50% { transform: scale(0.8); }
                100% { transform: scale(1); }
            }
            
            @keyframes cursorHover {
                0% { transform: rotate(0deg); }
                25% { transform: rotate(5deg); }
                75% { transform: rotate(-5deg); }
                100% { transform: rotate(0deg); }
            }
            
            .visual-container {
                position: relative;
                margin-top: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .visual-preview {
                width: 100%;
                display: block;
            }
        `;
        document.head.appendChild(styleElement);
    }

    // Function to update the visual monitoring display
    function updateVisualMonitor(step) {
        if (!visualData || visualData.screenshots.length === 0) {
            return;
        }

        // Ensure step is within bounds
        if (step < 0) step = 0;
        if (step >= visualData.screenshots.length) step = visualData.screenshots.length - 1;
        
        currentVisualStep = step;
        
        // Update screenshot
        const screenshotPath = `/user_data/${visualData.screenshots[step]}`;
        $('#current-screenshot').attr('src', screenshotPath);
        
        // Update description
        $('#visual-description').text(visualData.descriptions[step]);
        
        // Update step indicator
        $('#step-indicator').text(`${step + 1}/${visualData.screenshots.length}`);
        
        // Handle cursor position
        $('.cursor-indicator').remove();
        const cursorPos = visualData.cursor_positions[step];
        if (cursorPos) {
            const cursor = $('<div class="cursor-indicator"></div>');
            cursor.css({
                left: `${cursorPos.x}px`,
                top: `${cursorPos.y}px`
            });
            $('#current-screenshot-container').append(cursor);
        }
    }

    // Initialize visual monitoring controls
    function initVisualMonitoring() {
        $('#prev-step').click(function() {
            updateVisualMonitor(currentVisualStep - 1);
        });
        
        $('#next-step').click(function() {
            updateVisualMonitor(currentVisualStep + 1);
        });
    }

    // Modify the existing event source handler to handle visual data
    function setupEventSource(timestamp) {
        const eventSource = new EventSource(`/api/chat/stream?t=${timestamp}`);
        
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'visual_data') {
                // We received visual data, store it and show the visual monitor
                visualData = data;
                $('#visual-placeholder').hide();
                $('#visual-content').show();
                currentVisualStep = 0;
                updateVisualMonitor(0);
            } else if (data.token) {
                // ... existing token handling code ...
            } else if (data.status === 'completed') {
                // ... existing completion code ...
            }
        };
        
        // ... existing event source error handling ...
    }

    // Initialize everything when the document is ready
    $(document).ready(function() {
        // ... existing initialization code ...
        
        initVisualMonitoring();
        
        // Reset visual monitor when starting a new chat
        $('#send-button').click(function() {
            // ... existing send button code ...
            
            // Reset visual monitor
            visualData = null;
            $('#visual-content').hide();
            $('#visual-placeholder').show();
        });
    });
}); 