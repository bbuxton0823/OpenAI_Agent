#!/usr/bin/env python3
"""
WebSocket to TCP proxy for VNC connections.
This script allows the browser to connect to a VNC server via WebSockets.
"""

import sys
import signal
import subprocess
import os
import time
from pathlib import Path

def start_websockify():
    """Start the websockify proxy for VNC connections."""
    # Path to websockify script in the noVNC directory
    websockify_path = Path(__file__).parent / "static" / "vnc" / "utils" / "websockify"
    
    # Check if websockify exists
    if not websockify_path.exists():
        print(f"Error: websockify not found at {websockify_path}")
        return None
    
    # Start websockify to proxy WebSocket connections to VNC
    cmd = [
        sys.executable,
        str(websockify_path),
        "--web", str(Path(__file__).parent / "static" / "vnc"),
        "6081", "localhost:6080"
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        print(f"Started websockify proxy (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"Error starting websockify: {e}")
        return None

def stop_proxy(process):
    """Stop the websockify proxy process."""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
            print("Websockify proxy stopped")
        except subprocess.TimeoutExpired:
            process.kill()
            print("Websockify proxy killed")

if __name__ == "__main__":
    proxy_process = start_websockify()
    
    if not proxy_process:
        sys.exit(1)
    
    # Handle termination signals
    def signal_handler(sig, frame):
        print("Stopping websockify proxy...")
        stop_proxy(proxy_process)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping websockify proxy...")
        stop_proxy(proxy_process)
