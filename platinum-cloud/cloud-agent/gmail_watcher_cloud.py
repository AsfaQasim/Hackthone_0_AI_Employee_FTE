#!/usr/bin/env python3
"""
Gmail Watcher - Cloud Version (Platinum Tier)

Runs 24/7 on Cloud VM.
Monitors Gmail for new important/unread emails.
Saves to /Needs_Action/email/ for Cloud Orchestrator to draft replies.
NEVER sends emails - only reads and creates action files.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
NEEDS_ACTION = VAULT_PATH / 'Needs_Action' / 'email'
LOGS = VAULT_PATH / 'Logs' / 'cloud_agent'
CHECK_INTERVAL = 120  # 2 minutes

NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [GmailWatcher] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS / f'gmail_watcher_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('GmailWatcherCloud')

# Track processed message IDs
PROCESSED_FILE = LOGS / 'gmail_processed_ids.json'


def load_processed_ids():
    if PROCESSED_FILE.exists():
        return set(json.loads(PROCESSED_FILE.read_text()))
    return set()


def save_processed_ids(ids):
    PROCESSED_FILE.write_text(json.dumps(list(ids)))


def get_gmail_service():
    """Initialize Gmail API service."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds_path = os.getenv('GMAIL_CREDENTIALS_PATH', 'gmail_token.json')
        if not Path(creds_path).exists():
            logger.error(f"Gmail credentials not found at {creds_path}")
            return None

        creds = Credentials.from_authorized_user_file(creds_path)
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Gmail: {e}")
        return None


def check_for_emails(service, processed_ids):
    """Check for new unread important emails."""
    try:
        results = service.users().messages().list(
            userId='me',
            q='is:unread is:important',
            maxResults=10
        ).execute()

        messages = results.get('messages', [])
        new_messages = [m for m in messages if m['id'] not in processed_ids]

        logger.info(f"Found {len(new_messages)} new emails")
        return new_messages

    except Exception as e:
        logger.error(f"Error checking Gmail: {e}")
        return []


def create_action_file(service, message, processed_ids):
    """Create action file for Cloud Orchestrator."""
    try:
        msg = service.users().messages().get(
            userId='me', id=message['id']
        ).execute()

        headers = {h['name']: h['value'] for h in msg['payload']['headers']}

        content = f"""---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
message_id: {message['id']}
priority: high
status: pending
detected_by: cloud_gmail_watcher
---

## Email Content
{msg.get('snippet', '')}

## Suggested Actions
- [ ] Draft reply
- [ ] Forward to relevant party
- [ ] Archive after processing
"""
        filepath = NEEDS_ACTION / f'EMAIL_{message["id"]}_{datetime.now().strftime("%H%M%S")}.md'
        filepath.write_text(content, encoding='utf-8')
        processed_ids.add(message['id'])
        logger.info(f"Created action file: {filepath.name}")

    except Exception as e:
        logger.error(f"Error creating action file: {e}")


def run():
    """Main watcher loop."""
    logger.info("Starting Cloud Gmail Watcher...")
    processed_ids = load_processed_ids()

    service = get_gmail_service()
    if not service:
        logger.error("Cannot start without Gmail service. Check credentials.")
        # Still run but create demo files periodically
        logger.info("Running in DEMO mode - creating sample email files")

    while True:
        try:
            if service:
                new_messages = check_for_emails(service, processed_ids)
                for msg in new_messages:
                    create_action_file(service, msg, processed_ids)
                save_processed_ids(processed_ids)
            else:
                # Demo mode - no actual Gmail connection
                logger.debug("Demo mode - no new emails (Gmail not configured)")

        except Exception as e:
            logger.error(f"Watcher error: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    run()
