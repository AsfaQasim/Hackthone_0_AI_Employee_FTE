#!/usr/bin/env python3
"""
Cloud Orchestrator - Platinum Tier

Runs 24/7 on Oracle Cloud VM.
Handles: Email triage, social post drafts, Odoo draft actions.
NEVER sends/posts directly - always writes to /Pending_Approval/.

Architecture:
  Cloud Agent → Drafts → /Pending_Approval/ → Git Sync → Local Approves → /Approved/ → Local Sends
"""

import os
import sys
import time
import json
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
AGENT_MODE = os.getenv('AGENT_MODE', 'cloud')
DRAFT_ONLY = os.getenv('DRAFT_ONLY', 'true').lower() == 'true'
CHECK_INTERVAL = int(os.getenv('SYNC_INTERVAL', '60'))
HEALTH_PORT = int(os.getenv('HEALTH_CHECK_PORT', '8080'))

# Directories
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval'
IN_PROGRESS = VAULT_PATH / 'In_Progress' / 'cloud'
APPROVED = VAULT_PATH / 'Approved'
DONE = VAULT_PATH / 'Done'
UPDATES = VAULT_PATH / 'Updates'
LOGS = VAULT_PATH / 'Logs' / 'cloud_agent'

# Ensure directories exist
for d in [NEEDS_ACTION, PENDING_APPROVAL, IN_PROGRESS, APPROVED, DONE, UPDATES, LOGS]:
    d.mkdir(parents=True, exist_ok=True)
    for sub in ['email', 'social', 'accounting']:
        (NEEDS_ACTION / sub).mkdir(exist_ok=True)
        (PENDING_APPROVAL / sub).mkdir(exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CloudOrchestrator')


class CloudOrchestrator:
    """
    Cloud-side orchestrator that processes tasks in DRAFT-ONLY mode.

    Claim-by-move rule: Moves file from /Needs_Action to /In_Progress/cloud/
    to prevent Local agent from also picking it up.
    """

    def __init__(self):
        self.running = True
        self.stats = {
            'started': datetime.now().isoformat(),
            'tasks_processed': 0,
            'drafts_created': 0,
            'errors': 0,
            'last_check': None
        }
        logger.info(f"Cloud Orchestrator started (mode={AGENT_MODE}, draft_only={DRAFT_ONLY})")

    def claim_task(self, task_file: Path) -> Optional[Path]:
        """
        Claim a task using claim-by-move rule.
        First agent to move it to /In_Progress/<agent>/ owns it.
        """
        dest = IN_PROGRESS / task_file.name
        try:
            if dest.exists():
                return None  # Already claimed
            shutil.move(str(task_file), str(dest))
            logger.info(f"Claimed task: {task_file.name}")
            return dest
        except (FileNotFoundError, shutil.Error):
            # Another agent claimed it first
            return None

    def process_email_task(self, task_file: Path):
        """Process an email task - create draft reply."""
        content = task_file.read_text(encoding='utf-8')

        # Parse the email metadata
        lines = content.split('\n')
        from_addr = ''
        subject = ''
        body_lines = []
        in_body = False

        for line in lines:
            if line.startswith('from:'):
                from_addr = line.split(':', 1)[1].strip()
            elif line.startswith('subject:'):
                subject = line.split(':', 1)[1].strip()
            elif line.startswith('## Email Content'):
                in_body = True
            elif in_body and not line.startswith('## '):
                body_lines.append(line)

        email_body = '\n'.join(body_lines).strip()

        # Create draft reply
        draft_content = f"""---
type: email_draft_reply
original_from: {from_addr}
original_subject: {subject}
created_by: cloud_agent
created: {datetime.now().isoformat()}
status: pending_approval
action: send_email
---

# Draft Email Reply

**To:** {from_addr}
**Subject:** Re: {subject}

## Draft Reply

Thank you for your email regarding "{subject}".

I have received your message and will get back to you shortly with a detailed response.

Best regards,
[Your Name]

## Original Message
{email_body}

## Instructions
- Review this draft reply
- Edit if needed
- Move to /Approved/email/ to send
- Move to /Rejected/ to discard
"""
        # Write to Pending_Approval
        approval_file = PENDING_APPROVAL / 'email' / f'DRAFT_REPLY_{task_file.stem}_{datetime.now().strftime("%H%M%S")}.md'
        approval_file.write_text(draft_content, encoding='utf-8')
        logger.info(f"Created email draft: {approval_file.name}")
        self.stats['drafts_created'] += 1

    def process_social_task(self, task_file: Path):
        """Process a social media task - create draft post."""
        content = task_file.read_text(encoding='utf-8')

        # Create draft social post
        draft_content = f"""---
type: social_post_draft
platform: linkedin
created_by: cloud_agent
created: {datetime.now().isoformat()}
status: pending_approval
action: post_social_media
---

# Draft Social Media Post

## LinkedIn Post Draft

[AI-generated post content based on business goals]

Excited to share our latest developments in AI-powered business automation!

Our team has been working on innovative solutions that help businesses streamline their operations.

#AI #Business #Automation #Innovation

## Instructions
- Review and edit this draft
- Move to /Approved/social/ to publish
- Move to /Rejected/ to discard

## Original Request
{content}
"""
        approval_file = PENDING_APPROVAL / 'social' / f'DRAFT_POST_{task_file.stem}_{datetime.now().strftime("%H%M%S")}.md'
        approval_file.write_text(draft_content, encoding='utf-8')
        logger.info(f"Created social draft: {approval_file.name}")
        self.stats['drafts_created'] += 1

    def process_accounting_task(self, task_file: Path):
        """Process accounting task - create draft invoice/action."""
        content = task_file.read_text(encoding='utf-8')

        draft_content = f"""---
type: accounting_draft
created_by: cloud_agent
created: {datetime.now().isoformat()}
status: pending_approval
action: odoo_create_invoice
---

# Draft Accounting Action

## Proposed Action
Create invoice based on the following request.

## Details
{content}

## Instructions
- Review this accounting action
- Move to /Approved/accounting/ to execute in Odoo
- Move to /Rejected/ to discard
"""
        approval_file = PENDING_APPROVAL / 'accounting' / f'DRAFT_ACCOUNTING_{task_file.stem}_{datetime.now().strftime("%H%M%S")}.md'
        approval_file.write_text(draft_content, encoding='utf-8')
        logger.info(f"Created accounting draft: {approval_file.name}")
        self.stats['drafts_created'] += 1

    def process_needs_action(self):
        """Scan /Needs_Action/ folders and process tasks."""
        domains = {
            'email': self.process_email_task,
            'social': self.process_social_task,
            'accounting': self.process_accounting_task,
        }

        for domain, handler in domains.items():
            domain_dir = NEEDS_ACTION / domain
            if not domain_dir.exists():
                continue

            for task_file in sorted(domain_dir.glob('*.md')):
                # Claim the task
                claimed = self.claim_task(task_file)
                if not claimed:
                    continue

                try:
                    handler(claimed)
                    # Move to Done after processing
                    done_file = DONE / claimed.name
                    shutil.move(str(claimed), str(done_file))
                    self.stats['tasks_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing {claimed.name}: {e}")
                    self.stats['errors'] += 1
                    # Move back to Needs_Action on error
                    error_dest = NEEDS_ACTION / domain / claimed.name
                    shutil.move(str(claimed), str(error_dest))

    def write_cloud_status(self):
        """Write cloud agent status to /Updates/ for Local to merge."""
        status = {
            **self.stats,
            'last_check': datetime.now().isoformat(),
            'agent': 'cloud',
            'mode': AGENT_MODE,
            'draft_only': DRAFT_ONLY
        }

        status_file = UPDATES / 'cloud_status.json'
        status_file.write_text(json.dumps(status, indent=2), encoding='utf-8')

    def run(self):
        """Main orchestrator loop."""
        logger.info("Starting Cloud Orchestrator main loop...")

        # Start health check server in background
        health_thread = threading.Thread(target=self._start_health_server, daemon=True)
        health_thread.start()

        while self.running:
            try:
                self.process_needs_action()
                self.write_cloud_status()
                self.stats['last_check'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                self.stats['errors'] += 1

            time.sleep(CHECK_INTERVAL)

    def _start_health_server(self):
        """Simple HTTP health check endpoint."""
        orchestrator = self

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'healthy',
                        'agent': 'cloud',
                        **orchestrator.stats
                    }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress logs

        try:
            server = HTTPServer(('0.0.0.0', HEALTH_PORT), HealthHandler)
            logger.info(f"Health check running on port {HEALTH_PORT}")
            server.serve_forever()
        except Exception as e:
            logger.warning(f"Health server failed: {e}")


if __name__ == '__main__':
    orchestrator = CloudOrchestrator()
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Cloud Orchestrator stopped.")
