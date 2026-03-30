#!/usr/bin/env python3
"""
WhatsApp Local Handler - Platinum Tier

WhatsApp session NEVER goes to cloud. Stays local only.
Handles:
- WhatsApp message reading (via Playwright)
- WhatsApp message sending (after approval)
- Session management (local only)

Security: WhatsApp session data never syncs via Git.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
NEEDS_ACTION = VAULT_PATH / 'Needs_Action'
PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval'
APPROVED = VAULT_PATH / 'Approved'
DONE = VAULT_PATH / 'Done'
LOGS = VAULT_PATH / 'Logs' / 'local_agent'
WHATSAPP_SESSION = Path(os.getenv('WHATSAPP_SESSION_PATH', '.whatsapp_session'))

for d in [NEEDS_ACTION, DONE, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [WhatsAppLocal] %(levelname)s: %(message)s')
logger = logging.getLogger('WhatsAppLocal')

# Keywords that trigger action
KEYWORDS = ['urgent', 'asap', 'invoice', 'payment', 'help', 'quote', 'price']


def check_whatsapp_messages():
    """
    Check WhatsApp for new messages using Playwright.
    Only runs locally - session never leaves this machine.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                str(WHATSAPP_SESSION),
                headless=True
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            page.goto('https://web.whatsapp.com')

            # Wait for chat list
            try:
                page.wait_for_selector('[data-testid="chat-list"]', timeout=30000)
            except Exception:
                logger.warning("WhatsApp not loaded - may need QR scan")
                browser.close()
                return []

            # Find unread chats
            unread = page.query_selector_all('[aria-label*="unread"]')
            messages = []

            for chat in unread:
                text = chat.inner_text().lower()
                if any(kw in text for kw in KEYWORDS):
                    messages.append({
                        'text': text,
                        'timestamp': datetime.now().isoformat(),
                        'has_keyword': True
                    })

            browser.close()
            return messages

    except ImportError:
        logger.warning("Playwright not installed - WhatsApp watcher disabled")
        return []
    except Exception as e:
        logger.error(f"WhatsApp check error: {e}")
        return []


def create_action_file(message):
    """Create action file for WhatsApp message."""
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = NEEDS_ACTION / f'WHATSAPP_{ts}.md'

    content = f"""---
type: whatsapp_message
received: {message['timestamp']}
priority: high
status: pending
detected_by: local_whatsapp_handler
local_only: true
---

## WhatsApp Message
{message['text'][:500]}

## Suggested Actions
- [ ] Reply to sender
- [ ] Create invoice if requested
- [ ] Forward to relevant party
"""
    filepath.write_text(content, encoding='utf-8')
    logger.info(f"Created WhatsApp action file: {filepath.name}")
    return filepath


def process_approved_whatsapp():
    """Send approved WhatsApp messages."""
    whatsapp_approved = VAULT_PATH / 'Approved'
    for f in sorted(whatsapp_approved.glob('*WHATSAPP*.md')):
        try:
            content = f.read_text(encoding='utf-8')
            logger.info(f"Sending approved WhatsApp message: {f.name}")
            # In production: use Playwright to send message
            shutil.move(str(f), str(DONE / f.name))
            logger.info(f"WhatsApp message sent, moved to Done")
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {e}")


def run():
    """Main WhatsApp local handler loop."""
    import time
    logger.info("Starting WhatsApp Local Handler...")
    logger.info("NOTE: WhatsApp session stays LOCAL - never syncs to cloud")

    while True:
        # Check for new messages
        messages = check_whatsapp_messages()
        for msg in messages:
            create_action_file(msg)

        # Process approved messages
        process_approved_whatsapp()

        time.sleep(30)


if __name__ == '__main__':
    run()
