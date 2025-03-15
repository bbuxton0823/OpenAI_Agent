#!/usr/bin/env python3
"""
Simple script to start a websockify proxy for VNC connections.
"""

import subprocess
import sys
import os
import signal
import time

def start_websockify():
    """Start the websockify proxy for VNC connections."""
    # Use the installed websockify command
    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "vnc")
    
    # Start websockify to proxy WebSocket connections to VNC
    cmd = [
        "websockify",
        "--web", web_dir,
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

if __name__ == "__main__":
    proxy_process = start_websockify()
    
    if not proxy_process:
        sys.exit(1)
    
    # Handle termination signals
    def signal_handler(sig, frame):
        print("Stopping websockify proxy...")
        if proxy_process:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
                print("Websockify proxy stopped")
            except subprocess.TimeoutExpired:
                proxy_process.kill()
                print("Websockify proxy killed")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
