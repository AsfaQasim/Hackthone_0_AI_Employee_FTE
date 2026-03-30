#!/usr/bin/env python3
"""
Platinum Demo - Minimum Passing Gate

Simulates the complete Platinum flow:
1. Email arrives while Local is offline
2. Cloud drafts reply + writes approval file
3. When Local returns, user approves
4. Local executes send via MCP
5. Logs the action
6. Moves task to /Done

This can run entirely locally to DEMO the flow.
"""

import os
import sys
import time
import json
import shutil
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(os.getenv('VAULT_PATH', 'F:/hackthone_0'))

# Setup directories
dirs = {
    'needs_email': VAULT_PATH / 'Needs_Action' / 'email',
    'pending_email': VAULT_PATH / 'Pending_Approval' / 'email',
    'approved_email': VAULT_PATH / 'Approved' / 'email',
    'in_progress': VAULT_PATH / 'In_Progress' / 'cloud',
    'done': VAULT_PATH / 'Done',
    'logs': VAULT_PATH / 'Logs' / 'platinum_demo',
    'updates': VAULT_PATH / 'Updates',
}

for d in dirs.values():
    d.mkdir(parents=True, exist_ok=True)


def step(num, title):
    print(f"\n{'='*60}")
    print(f"  STEP {num}: {title}")
    print(f"{'='*60}")


def main():
    print("=" * 60)
    print("  PLATINUM TIER DEMO")
    print("  Email -> Cloud Draft -> Approve -> Local Send -> Done")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ─────────────────────────────────────
    # STEP 1: Email arrives (simulated)
    # ─────────────────────────────────────
    step(1, "Email Arrives (Cloud Gmail Watcher detects)")

    email_file = dirs['needs_email'] / f'EMAIL_demo_{timestamp}.md'
    email_content = f"""---
type: email
from: client_demo@example.com
subject: Need January Invoice
received: {datetime.now().isoformat()}
message_id: demo_{timestamp}
priority: high
status: pending
detected_by: cloud_gmail_watcher
---

## Email Content
Hi, can you please send me the invoice for January? I need it for my records.
Thanks!

## Suggested Actions
- [ ] Draft reply
- [ ] Forward to relevant party
"""
    email_file.write_text(email_content, encoding='utf-8')
    print(f"  Email detected: {email_file.name}")
    print(f"  From: client_demo@example.com")
    print(f"  Subject: Need January Invoice")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 2: Cloud Agent claims task (claim-by-move)
    # ─────────────────────────────────────
    step(2, "Cloud Agent Claims Task (claim-by-move rule)")

    claimed_file = dirs['in_progress'] / email_file.name
    shutil.move(str(email_file), str(claimed_file))
    print(f"  Moved: /Needs_Action/email/ -> /In_Progress/cloud/")
    print(f"  Cloud agent now owns this task")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 3: Cloud creates draft reply
    # ─────────────────────────────────────
    step(3, "Cloud Agent Creates Draft Reply (DRAFT ONLY - no send)")

    draft_file = dirs['pending_email'] / f'DRAFT_REPLY_demo_{timestamp}.md'
    draft_content = f"""---
type: email_draft_reply
original_from: client_demo@example.com
original_subject: Need January Invoice
created_by: cloud_agent
created: {datetime.now().isoformat()}
status: pending_approval
action: send_email
---

# Draft Email Reply

**To:** client_demo@example.com
**Subject:** Re: Need January Invoice

## Draft Reply

Dear Client,

Thank you for reaching out. I have prepared your January invoice and it is attached to this email.

Invoice Details:
- Invoice #: INV-2026-01
- Amount: $1,500.00
- Due Date: February 15, 2026

Please let me know if you have any questions.

Best regards,
AI Employee

## Instructions
- Review this draft reply
- Move to /Approved/email/ to send
- Move to /Rejected/ to discard
"""
    draft_file.write_text(draft_content, encoding='utf-8')

    # Move claimed file to done
    shutil.move(str(claimed_file), str(dirs['done'] / claimed_file.name))

    # Write cloud status update
    cloud_status = {
        'last_check': datetime.now().isoformat(),
        'tasks_processed': 1,
        'drafts_created': 1,
        'agent': 'cloud'
    }
    (dirs['updates'] / 'cloud_status.json').write_text(json.dumps(cloud_status, indent=2))

    print(f"  Draft created: {draft_file.name}")
    print(f"  Location: /Pending_Approval/email/")
    print(f"  Cloud status updated in /Updates/")
    print(f"  NOTE: Cloud NEVER sends - only drafts!")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 4: Git Sync (simulated)
    # ─────────────────────────────────────
    step(4, "Git Sync (Cloud -> Local)")

    print(f"  [Simulated] git commit + push from Cloud")
    print(f"  [Simulated] git pull on Local")
    print(f"  Draft file now visible on Local laptop")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 5: User approves (move to /Approved/)
    # ─────────────────────────────────────
    step(5, "User Approves (moves file to /Approved/email/)")

    approved_file = dirs['approved_email'] / draft_file.name
    shutil.move(str(draft_file), str(approved_file))
    print(f"  Moved: /Pending_Approval/email/ -> /Approved/email/")
    print(f"  User has approved sending this email")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 6: Local Agent sends email
    # ─────────────────────────────────────
    step(6, "Local Agent Sends Email (EXECUTE mode)")

    print(f"  Local Agent detected approved file")
    print(f"  SENDING email to: client_demo@example.com")
    print(f"  Subject: Re: Need January Invoice")
    print(f"  Status: SENT SUCCESSFULLY")

    # Log the action
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action_type': 'email_send',
        'actor': 'local_agent',
        'target': 'client_demo@example.com',
        'parameters': {'subject': 'Re: Need January Invoice'},
        'approval_status': 'approved',
        'approved_by': 'human',
        'result': 'success'
    }
    log_file = dirs['logs'] / f'actions_{datetime.now().strftime("%Y%m%d")}.json'
    log_file.write_text(json.dumps([log_entry], indent=2))

    print(f"  Action logged: {log_file.name}")
    time.sleep(1)

    # ─────────────────────────────────────
    # STEP 7: Move to /Done/
    # ─────────────────────────────────────
    step(7, "Task Complete -> /Done/")

    done_file = dirs['done'] / approved_file.name
    shutil.move(str(approved_file), str(done_file))
    print(f"  Moved: /Approved/email/ -> /Done/")
    print(f"  Task fully complete!")
    time.sleep(1)

    # ─────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  PLATINUM DEMO COMPLETE!")
    print(f"{'='*60}")
    print(f"""
  Flow completed:
    1. Email arrived        -> /Needs_Action/email/
    2. Cloud claimed task   -> /In_Progress/cloud/
    3. Cloud drafted reply  -> /Pending_Approval/email/
    4. Git synced           -> Cloud -> Local
    5. User approved        -> /Approved/email/
    6. Local sent email     -> via MCP
    7. Task done            -> /Done/
    8. Action logged        -> /Logs/

  Files created:
    - {dirs['done']}/{email_file.name}
    - {done_file}
    - {log_file}
    - {dirs['updates']}/cloud_status.json

  KEY POINT:
    Cloud = DRAFT only (never sends)
    Local = EXECUTE (after human approval)
    Secrets = NEVER leave local machine
""")


if __name__ == '__main__':
    main()
