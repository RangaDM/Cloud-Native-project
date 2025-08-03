#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend files
This allows the frontend to make API calls to the microservices
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def main():
    # Get port from environment or use default
    PORT = int(os.getenv('PORT', 8080))
    
    # Create a custom handler that serves files from the frontend directory
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # Get the directory where this script is located
            # super().__init__(*args, directory=".", **kwargs)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            super().__init__(*args, directory=script_dir, **kwargs)
        
        def end_headers(self):
            # Add CORS headers to allow API calls
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept')
            super().end_headers()
        
        def do_OPTIONS(self):
            # Handle preflight requests
            self.send_response(200)
            self.end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"🌐 Frontend server started at http://localhost:{PORT}")
            print(f"📁 Serving files from: {script_dir}")
            print(f"🔗 Make sure your microservices are running on ports 8001, 8002, and 8003")
            print(f"⏹️  Press Ctrl+C to stop the server")
            print(f"\n🎯 Open your browser and visit: http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port:")
            print(f"   python serve_frontend.py --port 8081")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 