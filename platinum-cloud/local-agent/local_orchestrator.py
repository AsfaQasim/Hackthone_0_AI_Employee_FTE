#!/usr/bin/env python3
"""
Local Orchestrator - Platinum Tier

Runs on YOUR laptop when you're online.
Handles:
  - Watching /Approved/ folder and EXECUTING actions (send email, post social)
  - WhatsApp session (stays local, never goes to cloud)
  - Banking/Payment actions (stays local)
  - Merging Cloud updates into Dashboard.md
  - Moving completed tasks to /Done/

Security: This is the ONLY agent that can SEND/POST/PAY.
"""

import os
import sys
import time
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
APPROVED = VAULT_PATH / 'Approved'
PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval'
DONE = VAULT_PATH / 'Done'
UPDATES = VAULT_PATH / 'Updates'
LOGS = VAULT_PATH / 'Logs' / 'local_agent'
DASHBOARD = VAULT_PATH / 'Dashboard.md'

CHECK_INTERVAL = 30  # seconds

# Ensure directories
for d in [APPROVED, DONE, UPDATES, LOGS]:
    d.mkdir(parents=True, exist_ok=True)
    for sub in ['email', 'social', 'accounting']:
        (APPROVED / sub).mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [LocalAgent] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS / f'local_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LocalOrchestrator')


class LocalOrchestrator:
    """
    Local-side orchestrator. Executes approved actions.
    Single-writer for Dashboard.md.
    """

    def __init__(self):
        self.stats = {
            'started': datetime.now().isoformat(),
            'actions_executed': 0,
            'emails_sent': 0,
            'posts_published': 0,
            'errors': 0
        }
        logger.info("Local Orchestrator started")

    def process_approved_emails(self):
        """Execute approved email drafts - SEND the email."""
        email_dir = APPROVED / 'email'
        for f in sorted(email_dir.glob('*.md')):
            try:
                content = f.read_text(encoding='utf-8')
                logger.info(f"Executing approved email: {f.name}")

                # Parse email details from draft
                to_addr = self._extract_field(content, 'original_from') or self._extract_field(content, 'To')
                subject = self._extract_field(content, 'original_subject') or self._extract_field(content, 'Subject')

                # Extract reply body
                reply_body = self._extract_section(content, '## Draft Reply')

                if to_addr and reply_body:
                    # Send via MCP or direct API
                    success = self._send_email(to_addr, f"Re: {subject}", reply_body)
                    if success:
                        self.stats['emails_sent'] += 1
                        self._log_action('email_send', {
                            'to': to_addr, 'subject': subject, 'status': 'sent'
                        })

                # Move to Done
                shutil.move(str(f), str(DONE / f.name))
                self.stats['actions_executed'] += 1
                logger.info(f"Email sent and moved to Done: {f.name}")

            except Exception as e:
                logger.error(f"Error processing email {f.name}: {e}")
                self.stats['errors'] += 1

    def process_approved_social(self):
        """Execute approved social media posts - PUBLISH."""
        social_dir = APPROVED / 'social'
        for f in sorted(social_dir.glob('*.md')):
            try:
                content = f.read_text(encoding='utf-8')
                logger.info(f"Publishing approved social post: {f.name}")

                # Extract post content
                post_content = self._extract_section(content, '## LinkedIn Post Draft')

                if post_content:
                    success = self._post_social(post_content)
                    if success:
                        self.stats['posts_published'] += 1
                        self._log_action('social_post', {
                            'platform': 'linkedin', 'status': 'published'
                        })

                shutil.move(str(f), str(DONE / f.name))
                self.stats['actions_executed'] += 1

            except Exception as e:
                logger.error(f"Error posting social {f.name}: {e}")
                self.stats['errors'] += 1

    def process_approved_accounting(self):
        """Execute approved accounting actions in Odoo."""
        acc_dir = APPROVED / 'accounting'
        for f in sorted(acc_dir.glob('*.md')):
            try:
                content = f.read_text(encoding='utf-8')
                logger.info(f"Executing approved accounting action: {f.name}")

                # Execute in Odoo via MCP server
                self._execute_odoo_action(content)

                shutil.move(str(f), str(DONE / f.name))
                self.stats['actions_executed'] += 1
                self._log_action('odoo_action', {'file': f.name, 'status': 'executed'})

            except Exception as e:
                logger.error(f"Error with accounting {f.name}: {e}")
                self.stats['errors'] += 1

    def merge_cloud_updates(self):
        """Merge Cloud Agent updates into Dashboard.md (single-writer rule)."""
        status_file = UPDATES / 'cloud_status.json'
        if not status_file.exists():
            return

        try:
            cloud_status = json.loads(status_file.read_text())

            # Count pending approvals
            pending_email = len(list((PENDING_APPROVAL / 'email').glob('*.md')))
            pending_social = len(list((PENDING_APPROVAL / 'social').glob('*.md')))
            pending_acc = len(list((PENDING_APPROVAL / 'accounting').glob('*.md')))

            dashboard_content = f"""---
updated: {datetime.now().isoformat()}
updated_by: local_agent
---

# AI Employee Dashboard

## System Status
- **Cloud Agent**: {'Online' if cloud_status.get('last_check') else 'Offline'}
- **Local Agent**: Online
- **Last Cloud Sync**: {cloud_status.get('last_check', 'N/A')}
- **Cloud Tasks Processed**: {cloud_status.get('tasks_processed', 0)}
- **Cloud Drafts Created**: {cloud_status.get('drafts_created', 0)}

## Pending Approvals
- **Email Drafts**: {pending_email} pending
- **Social Posts**: {pending_social} pending
- **Accounting**: {pending_acc} pending

## Local Agent Stats
- **Actions Executed**: {self.stats['actions_executed']}
- **Emails Sent**: {self.stats['emails_sent']}
- **Posts Published**: {self.stats['posts_published']}
- **Errors**: {self.stats['errors']}

## Recent Activity
{self._get_recent_done()}
"""
            DASHBOARD.write_text(dashboard_content, encoding='utf-8')

        except Exception as e:
            logger.error(f"Error merging updates: {e}")

    def _send_email(self, to, subject, body):
        """Send email via Gmail API or MCP."""
        logger.info(f"SENDING email to {to}: {subject}")
        # In production, use Gmail API or email MCP server
        # For now, log the action
        return True

    def _post_social(self, content):
        """Post to social media via MCP."""
        logger.info(f"POSTING to social media: {content[:50]}...")
        # In production, use social media MCP server
        return True

    def _execute_odoo_action(self, content):
        """Execute Odoo action via MCP."""
        logger.info(f"EXECUTING Odoo action")
        # In production, use Odoo MCP server
        return True

    def _extract_field(self, content, field):
        """Extract a field value from markdown frontmatter or content."""
        for line in content.split('\n'):
            if line.strip().startswith(f'{field}:'):
                return line.split(':', 1)[1].strip()
            if line.strip().startswith(f'**{field}:**'):
                return line.split(':**', 1)[1].strip()
        return ''

    def _extract_section(self, content, header):
        """Extract content under a markdown header."""
        lines = content.split('\n')
        capture = False
        section = []
        for line in lines:
            if line.strip().startswith(header):
                capture = True
                continue
            elif capture and line.startswith('## '):
                break
            elif capture:
                section.append(line)
        return '\n'.join(section).strip()

    def _get_recent_done(self):
        """Get recent completed tasks for dashboard."""
        done_files = sorted(DONE.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)[:5]
        lines = []
        for f in done_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            lines.append(f"- [{mtime}] {f.stem}")
        return '\n'.join(lines) if lines else "- No recent activity"

    def _log_action(self, action_type, data):
        """Log action for audit trail."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'local_agent',
            'data': data
        }
        log_file = LOGS / f'actions_{datetime.now().strftime("%Y%m%d")}.json'

        entries = []
        if log_file.exists():
            try:
                entries = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                entries = []

        entries.append(log_entry)
        log_file.write_text(json.dumps(entries, indent=2), encoding='utf-8')

    def run(self):
        """Main loop."""
        logger.info("Starting Local Orchestrator main loop...")

        while True:
            try:
                # Process approved actions
                self.process_approved_emails()
                self.process_approved_social()
                self.process_approved_accounting()

                # Merge cloud updates into dashboard
                self.merge_cloud_updates()

            except Exception as e:
                logger.error(f"Local orchestrator error: {e}")
                self.stats['errors'] += 1

            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    orchestrator = LocalOrchestrator()
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Local Orchestrator stopped.")
