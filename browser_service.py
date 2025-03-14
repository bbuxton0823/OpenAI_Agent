from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
from pathlib import Path
import os
import threading
import base64
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Create data directory
DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Global driver instance for persistent browser session
driver = None
driver_lock = threading.Lock()

# Add a function to initialize the driver
def initialize_driver():
    global driver
    try:
        # Set up Firefox options - NOT headless for visual browsing
        firefox_options = Options()
        # Not headless for visual browsing
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--width=1280")
        firefox_options.add_argument("--height=800")
        
        # Use the DISPLAY environment variable set by supervisord
        # This ensures the browser is visible in the VNC session
        print("Initializing Firefox driver with display:", os.environ.get('DISPLAY', ':1'))
        
        # Initialize the Firefox driver
        driver = webdriver.Firefox(options=firefox_options)
        
        # Set window size
        driver.set_window_size(1280, 800)
        print("Firefox driver initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing driver: {str(e)}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/browse', methods=['POST'])
def browse_website():
    """Browse a website with visual feedback"""
    global driver
    
    data = request.json
    url = data.get('url', 'https://www.example.com')
    
    try:
        with driver_lock:
            if driver is None:
                success = initialize_driver()
                if not success:
                    return jsonify({
                        "error": "Failed to initialize WebDriver",
                        "url": url
                    }), 500
            
            # Create directory for screenshots
            timestamp = int(time.time())
            visual_dir = SCREENSHOTS_DIR / f"visual_{timestamp}"
            visual_dir.mkdir(exist_ok=True)
            
            try:
                # Navigate to URL
                driver.get(url)
                time.sleep(2)
            except Exception as e:
                # If navigation fails, try to reinitialize the driver
                print(f"Navigation failed: {str(e)}, reinitializing driver")
                try:
                    if driver:
                        driver.quit()
                except:
                    pass
                
                driver = None
                success = initialize_driver()
                if not success:
                    return jsonify({
                        "error": "Failed to reinitialize WebDriver after navigation error",
                        "url": url
                    }), 500
                
                # Try navigation again
                driver.get(url)
                time.sleep(2)
            
            # Inject cursor visualization
            cursor_js = """
            var cursor = document.createElement('div');
            cursor.id = 'selenium-mouse-cursor';
            cursor.style.position = 'absolute';
            cursor.style.width = '20px';
            cursor.style.height = '20px';
            cursor.style.borderRadius = '10px';
            cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
            cursor.style.zIndex = '9999';
            cursor.style.pointerEvents = 'none';
            document.body.appendChild(cursor);
            
            window.addEventListener('mousemove', function(e) {
                cursor.style.left = e.clientX + 'px';
                cursor.style.top = e.clientY + 'px';
            });
            """
            driver.execute_script(cursor_js)
            
            # Take initial screenshot
            initial_screenshot_path = visual_dir / f"step_0_{timestamp}.png"
            driver.save_screenshot(str(initial_screenshot_path))
            
            # Create action chain for mouse movements
            actions = ActionChains(driver)
            
            # Lists to store visual feedback data
            screenshots = [str(initial_screenshot_path)]
            descriptions = [f"Initial page load of {url}"]
            cursor_positions = [None]  # No cursor for initial view
            interactions = ["page_load"]
            
            # Find interactive elements
            interactive_elements = []
            try:
                # First 5 links that are visible
                links = driver.find_elements(By.TAG_NAME, "a")
                visible_links = [
                    link for link in links[:20]
                    if link.is_displayed()
                ]
                interactive_elements.extend(visible_links[:5])
                
                # First 3 buttons that are visible
                buttons = driver.find_elements(By.TAG_NAME, "button")
                visible_buttons = [
                    button for button in buttons[:10]
                    if button.is_displayed()
                ]
                interactive_elements.extend(visible_buttons[:3])
                
                # First 3 inputs that are visible
                inputs = driver.find_elements(By.TAG_NAME, "input")
                visible_inputs = [
                    input_elem for input_elem in inputs[:10]
                    if input_elem.is_displayed()
                ]
                interactive_elements.extend(visible_inputs[:3])
            except Exception as e:
                print(f"Error finding elements: {e}")
            
            # Limit to 8 elements total
            interactive_elements = interactive_elements[:8]
            
            # First, do a general page scroll
            for scroll_step in range(3):
                # Scroll down smoothly
                driver.execute_script(
                    f"""window.scrollTo({{
                        top: {(scroll_step + 1) * 300},
                        behavior: 'smooth'
                    }});"""
                )
                time.sleep(1)
                
                # Take screenshot after scrolling
                scroll_path = visual_dir / f"scroll_{scroll_step+1}_{timestamp}.png"
                driver.save_screenshot(str(scroll_path))
                screenshots.append(str(scroll_path))
                descriptions.append(
                    f"Scrolling down to explore content (step {scroll_step+1})"
                )
                cursor_positions.append({
                    "x": 640,
                    "y": 300 + (scroll_step * 100)
                })
                interactions.append("scroll")
            
            # Scroll back to top
            driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
            time.sleep(1)
            
            # Interact with elements
            for i, element in enumerate(interactive_elements):
                try:
                    # Check if element is still visible
                    if not element.is_displayed():
                        continue
                    
                    # Scroll element into view
                    driver.execute_script(
                        """arguments[0].scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });""",
                        element
                    )
                    time.sleep(1)
                    
                    # Take screenshot after scrolling
                    scroll_path = visual_dir / f"step_{i+1}_scroll_{timestamp}.png"
                    driver.save_screenshot(str(scroll_path))
                    screenshots.append(str(scroll_path))
                    
                    # Get element description
                    tag_name = element.tag_name
                    element_text = element.text[:30] if element.text else ""
                    element_type = element.get_attribute("type") or ""
                    
                    if tag_name == "a":
                        descriptions.append(f"Scrolled to link: {element_text}")
                    elif tag_name == "button":
                        descriptions.append(f"Scrolled to button: {element_text}")
                    elif tag_name == "input":
                        descriptions.append(f"Scrolled to input field of type: {element_type}")
                    else:
                        descriptions.append(f"Scrolled to {tag_name} element")
                    
                    interactions.append("scroll_to_element")
                    
                    # Get element position for cursor tracking
                    rect = driver.execute_script("""
                        var rect = arguments[0].getBoundingClientRect();
                        return {
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            width: rect.width,
                            height: rect.height
                        };
                    """, element)
                    
                    cursor_x = rect['x']
                    cursor_y = rect['y']
                    
                    # Add cursor position
                    cursor_positions.append({
                        "x": cursor_x,
                        "y": cursor_y
                    })
                    
                    # Move cursor to element
                    actions.move_to_element(element).perform()
                    time.sleep(0.5)
                    
                    # Take screenshot with cursor hovering
                    hover_path = visual_dir / f"step_{i+1}_hover_{timestamp}.png"
                    driver.save_screenshot(str(hover_path))
                    screenshots.append(str(hover_path))
                    
                    if tag_name == "a":
                        descriptions.append(f"Hovering over link: {element_text}")
                        interactions.append("hover_link")
                    elif tag_name == "button":
                        descriptions.append(f"Hovering over button: {element_text}")
                        interactions.append("hover_button")
                    elif tag_name == "input":
                        descriptions.append(f"Hovering over input field of type: {element_type}")
                        interactions.append("hover_input")
                    else:
                        descriptions.append(f"Hovering over {tag_name} element")
                        interactions.append("hover_element")
                    
                    # Add cursor position
                    cursor_positions.append({
                        "x": cursor_x,
                        "y": cursor_y
                    })
                    
                    # For input elements, simulate typing
                    if (tag_name == "input" and
                            element.is_displayed() and
                            element.is_enabled()):
                        element_type = element.get_attribute("type") or ""
                        if element_type in ["text", "search", "email", "password"]:
                            try:
                                # Click on the input field
                                actions.click().perform()
                                time.sleep(0.3)
                                
                                # Take screenshot after clicking
                                click_path = visual_dir / f"step_{i+1}_click_{timestamp}.png"
                                driver.save_screenshot(str(click_path))
                                
                                # Add to visual feedback data
                                screenshots.append(str(click_path))
                                descriptions.append(f"Clicked on {element_type} field")
                                cursor_positions.append({"x": cursor_x, "y": cursor_y})
                                interactions.append("click_input")
                                
                                # Clear the field
                                element.clear()
                                time.sleep(0.3)
                                
                                # Determine what text to type
                                sample_text = "Sample text for demonstration"
                                if "search" in element_type.lower() or (element.get_attribute("name") and "search" in element.get_attribute("name").lower()):
                                    sample_text = "search query example"
                                elif "email" in element_type.lower():
                                    sample_text = "example@email.com"
                                elif "password" in element_type.lower():
                                    sample_text = "••••••••"
                                
                                # Type sample text character by character
                                for char in sample_text:
                                    element.send_keys(char)
                                    time.sleep(0.1)
                                
                                # Take screenshot after typing
                                typing_path = visual_dir / f"step_{i+1}_typing_{timestamp}.png"
                                driver.save_screenshot(str(typing_path))
                                screenshots.append(str(typing_path))
                                descriptions.append(f"Typing in {element_type}: '{sample_text}'")
                                interactions.append("typing")
                                cursor_positions.append({"x": cursor_x, "y": cursor_y})
                            except Exception as e:
                                print(f"Error typing in element {i}: {e}")
                    
                    # For links and buttons, simulate clicking on the last one
                    elif tag_name in ["a", "button"] and i == len(interactive_elements) - 1:
                        try:
                            # Take screenshot before clicking
                            pre_click_path = visual_dir / f"step_{i+1}_pre_click_{timestamp}.png"
                            driver.save_screenshot(str(pre_click_path))
                            screenshots.append(str(pre_click_path))
                            descriptions.append(f"About to click {tag_name}: {element_text}")
                            cursor_positions.append({"x": cursor_x, "y": cursor_y})
                            interactions.append("pre_click")
                            
                            # Click the element
                            actions.click().perform()
                            time.sleep(2)
                            
                            # Take screenshot after clicking
                            post_click_path = visual_dir / f"step_{i+1}_post_click_{timestamp}.png"
                            driver.save_screenshot(str(post_click_path))
                            screenshots.append(str(post_click_path))
                            descriptions.append(f"After clicking {tag_name}: {element_text}")
                            cursor_positions.append(None)
                            interactions.append("post_click")
                        except Exception as e:
                            print(f"Error clicking element {i}: {e}")
                except Exception as e:
                    print(f"Error interacting with element {i}: {e}")
            
            # Take final screenshot
            final_screenshot_path = visual_dir / f"step_final_{timestamp}.png"
            driver.save_screenshot(str(final_screenshot_path))
            screenshots.append(str(final_screenshot_path))
            descriptions.append("Final view of the page")
            cursor_positions.append(None)
            interactions.append("final_view")
            
            # Get page title and content
            title = driver.title
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Limit text content
            if len(body_text) > 5000:
                body_text = body_text[:5000] + "... [content truncated]"
            
            # Close the browser
            driver.quit()
            
            # Create relative paths for frontend
            relative_screenshots = [
                str(Path(s).relative_to(DATA_DIR)) for s in screenshots
            ]
            
            # Prepare result
            result_data = {
                "title": title,
                "url": url,
                "screenshots": relative_screenshots,
                "descriptions": descriptions,
                "cursor_positions": cursor_positions,
                "interactions": interactions,
                "content_preview": (
                    body_text[:500] + "..." if len(body_text) > 500 else body_text
                ),
                "timestamp": timestamp
            }
            
            return jsonify(result_data)
    
    except Exception as e:
        return jsonify({
            "error": f"Error browsing website: {str(e)}",
            "url": url
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 