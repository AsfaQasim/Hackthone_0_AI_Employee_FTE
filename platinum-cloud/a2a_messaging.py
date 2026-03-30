#!/usr/bin/env python3
"""
A2A (Agent-to-Agent) Messaging - Platinum Tier Phase 2

Replaces some file handoffs with direct HTTP messages between agents.
Vault remains the audit record for all messages.

Architecture:
  Cloud Agent <--HTTP--> Local Agent
  Both agents also write to vault as backup/audit

Message Types:
  - task_assignment: Cloud assigns task to Local
  - task_complete: Local reports completion
  - status_update: Either agent reports status
  - approval_request: Cloud requests Local approval
  - approval_response: Local responds to approval request
"""

import os
import json
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
AGENT_MODE = os.getenv('AGENT_MODE', 'local')  # 'cloud' or 'local'
A2A_PORT = int(os.getenv('A2A_PORT', '9090'))
REMOTE_AGENT_URL = os.getenv('REMOTE_AGENT_URL', '')  # URL of the other agent
SIGNALS_DIR = VAULT_PATH / 'Signals'
SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [A2A] %(levelname)s: %(message)s')
logger = logging.getLogger('A2A')


class A2AMessage:
    """Agent-to-Agent message format."""

    def __init__(self, msg_type, sender, payload, msg_id=None):
        self.id = msg_id or f"{sender}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        self.type = msg_type
        self.sender = sender
        self.timestamp = datetime.now().isoformat()
        self.payload = payload

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'sender': self.sender,
            'timestamp': self.timestamp,
            'payload': self.payload
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data):
        return cls(
            msg_type=data['type'],
            sender=data['sender'],
            payload=data['payload'],
            msg_id=data.get('id')
        )


class A2AHandler(BaseHTTPRequestHandler):
    """HTTP handler for receiving A2A messages."""

    agent = None  # Set by A2AAgent

    def do_POST(self):
        if self.path == '/a2a/message':
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)

            try:
                data = json.loads(body)
                msg = A2AMessage.from_dict(data)
                self.agent.handle_incoming(msg)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'received', 'id': msg.id}).encode())

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/a2a/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'agent': self.agent.agent_name,
                'status': 'online',
                'messages_received': self.agent.messages_received,
                'messages_sent': self.agent.messages_sent
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs


class A2AAgent:
    """Agent-to-Agent messaging system."""

    def __init__(self, agent_name, port=A2A_PORT, remote_url=''):
        self.agent_name = agent_name
        self.port = port
        self.remote_url = remote_url
        self.messages_received = 0
        self.messages_sent = 0
        self.message_handlers = {}
        self.server = None

    def register_handler(self, msg_type, handler_func):
        """Register a handler for a specific message type."""
        self.message_handlers[msg_type] = handler_func

    def send_message(self, msg_type, payload):
        """Send message to remote agent."""
        msg = A2AMessage(msg_type, self.agent_name, payload)

        # Always write to vault as audit record
        signal_file = SIGNALS_DIR / f'{msg.id}.json'
        signal_file.write_text(msg.to_json(), encoding='utf-8')

        # Try HTTP delivery
        if self.remote_url:
            try:
                req = Request(
                    f'{self.remote_url}/a2a/message',
                    data=msg.to_json().encode(),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                resp = urlopen(req, timeout=10)
                self.messages_sent += 1
                logger.info(f"Sent A2A message: {msg.type} -> {self.remote_url}")
                return True
            except URLError as e:
                logger.warning(f"HTTP delivery failed ({e}), message saved to vault")
                return False
        else:
            logger.info(f"No remote URL configured, message saved to vault only: {msg.type}")
            return False

    def handle_incoming(self, msg):
        """Handle received A2A message."""
        self.messages_received += 1
        logger.info(f"Received A2A message: {msg.type} from {msg.sender}")

        # Save to vault as audit
        signal_file = SIGNALS_DIR / f'{msg.id}.json'
        signal_file.write_text(msg.to_json(), encoding='utf-8')

        # Call registered handler
        handler = self.message_handlers.get(msg.type)
        if handler:
            handler(msg)
        else:
            logger.warning(f"No handler registered for message type: {msg.type}")

    def start_server(self):
        """Start HTTP server for receiving messages."""
        A2AHandler.agent = self
        self.server = HTTPServer(('0.0.0.0', self.port), A2AHandler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"A2A server started on port {self.port}")

    def stop_server(self):
        if self.server:
            self.server.shutdown()


# Example usage
def demo():
    """Demo A2A messaging between Cloud and Local agents."""
    print("=" * 55)
    print("  A2A MESSAGING DEMO")
    print("=" * 55)

    # Create two agents (simulating Cloud and Local)
    cloud = A2AAgent('cloud_agent', port=9090, remote_url='http://localhost:9091')
    local = A2AAgent('local_agent', port=9091, remote_url='http://localhost:9090')

    # Register handlers
    def on_approval_request(msg):
        print(f"  [LOCAL] Received approval request: {msg.payload.get('description')}")
        # Auto-approve for demo
        local.send_message('approval_response', {
            'original_id': msg.id,
            'approved': True,
            'approved_by': 'human'
        })

    def on_approval_response(msg):
        print(f"  [CLOUD] Received approval: approved={msg.payload.get('approved')}")

    def on_task_complete(msg):
        print(f"  [CLOUD] Task completed: {msg.payload.get('task')}")

    local.register_handler('approval_request', on_approval_request)
    cloud.register_handler('approval_response', on_approval_response)
    cloud.register_handler('task_complete', on_task_complete)

    # Start servers
    cloud.start_server()
    local.start_server()
    time.sleep(1)

    # Cloud sends approval request
    print("\n  [CLOUD] Sending approval request...")
    cloud.send_message('approval_request', {
        'description': 'Send invoice to Client Alpha - $1500',
        'action': 'send_email',
        'amount': 1500
    })
    time.sleep(1)

    # Local sends task complete
    print("\n  [LOCAL] Sending task complete...")
    local.send_message('task_complete', {
        'task': 'Email sent to Client Alpha',
        'status': 'success'
    })
    time.sleep(1)

    # Show signals
    print(f"\n  Signals saved to /Signals/:")
    for f in sorted(SIGNALS_DIR.glob('*.json')):
        data = json.loads(f.read_text())
        print(f"    - {data['type']} from {data['sender']}")

    print(f"\n  Cloud: sent={cloud.messages_sent}, received={cloud.messages_received}")
    print(f"  Local: sent={local.messages_sent}, received={local.messages_received}")

    # Cleanup
    cloud.stop_server()
    local.stop_server()

    print("\n  A2A Demo Complete!")
    print("=" * 55)


if __name__ == '__main__':
    demo()
