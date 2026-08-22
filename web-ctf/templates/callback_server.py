#!/usr/bin/env python3
"""Simple HTTP callback server for blind XSS/SSRF CTF challenges.

Logs all incoming requests with full details to callbacks.log.
Serves static files from current directory (e.g. xss.js, portfolio.html).
Supports custom route handlers for redirects or dynamic responses.

Usage:
  python3 callback_server.py
  # Then expose via tunnel: npx localtunnel --port 8000 --subdomain bxss
"""

import http.server
import socketserver
from datetime import datetime
import sys

PORT = 8000
LOG_FILE = 'callbacks.log'

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        """Log all requests with full context to callbacks.log."""
        timestamp = datetime.utcnow().isoformat() + 'Z'
        client_ip = self.client_address[0]
        ua = self.headers.get('User-Agent', '')
        referer = self.headers.get('Referer', '')
        xff = self.headers.get('X-Forwarded-For', '')
        real_ip = self.headers.get('X-Real-IP', '')
        cf_ip = self.headers.get('CF-Connecting-IP', '')
        
        log_line = (
            f"[{timestamp}] {client_ip} {self.command} {self.path} "
            f"UA={ua} Referer={referer} XFF={xff} RealIP={real_ip} CFIP={cf_ip}\n"
        )
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_line)
        
        # Also print to stdout for live monitoring
        sys.stdout.write(log_line)
        sys.stdout.flush()
    
    def do_GET(self):
        """Handle GET requests. Serves static files or custom routes."""
        # Custom route example: redirect handler
        # if self.path.startswith('/r?to='):
        #     target = self.path.split('to=', 1)[1]
        #     self.send_response(302)
        #     self.send_header('Location', target)
        #     self.end_headers()
        #     return
        
        # Default: serve static files from current directory
        return super().do_GET()
    
    def do_POST(self):
        """Handle POST requests. Log and return 200."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='replace')
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] POST body: {body}\n")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

if __name__ == '__main__':
    with socketserver.TCPServer(('', PORT), CallbackHandler) as httpd:
        print(f"Callback server running on port {PORT}")
        print(f"Logging to {LOG_FILE}")
        httpd.serve_forever()
