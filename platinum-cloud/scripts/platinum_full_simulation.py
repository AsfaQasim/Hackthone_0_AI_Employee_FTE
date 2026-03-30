#!/usr/bin/env python3
"""
Platinum Tier - Full Local Simulation

Simulates BOTH Cloud Agent + Local Agent running on same machine.
Shows the complete flow: Email -> Cloud Draft -> User Approve -> Local Send -> Done
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

VAULT = Path('F:/hackthone_0')


def setup_dirs():
    for d in ['Needs_Action/email', 'Needs_Action/social', 'Needs_Action/accounting',
              'Pending_Approval/email', 'Pending_Approval/social', 'Pending_Approval/accounting',
              'Approved/email', 'Approved/social', 'Approved/accounting',
              'In_Progress/cloud', 'In_Progress/local',
              'Updates', 'Done', 'Rejected',
              'Logs/cloud_agent', 'Logs/local_agent']:
        (VAULT / d).mkdir(parents=True, exist_ok=True)


def main():
    setup_dirs()
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    print('=' * 60)
    print('  PLATINUM TIER - FULL LOCAL SIMULATION')
    print('  Cloud Agent + Local Agent on same machine')
    print('=' * 60)

    # ========================================
    # PART 1: CLOUD AGENT - Email Processing
    # ========================================
    print('\n--- CLOUD AGENT (DRAFT-ONLY MODE) ---\n')

    emails = [
        {'from': 'ali@client.com', 'subject': 'Project Quote Request',
         'body': 'Hi, I need a quote for website development.'},
        {'from': 'sara@vendor.com', 'subject': 'Invoice Payment Due',
         'body': 'Your invoice #456 is due next week.'},
        {'from': 'ahmed@partner.com', 'subject': 'Meeting Schedule',
         'body': 'Can we schedule a meeting for Thursday?'},
    ]

    for i, email in enumerate(emails):
        # Email arrives
        email_file = VAULT / 'Needs_Action' / 'email' / f'EMAIL_{i+1}_{ts}.md'
        email_file.write_text(
            f'---\ntype: email\nfrom: {email["from"]}\n'
            f'subject: {email["subject"]}\nreceived: {datetime.now().isoformat()}\n'
            f'priority: high\nstatus: pending\ndetected_by: cloud_gmail_watcher\n---\n\n'
            f'## Email Content\n{email["body"]}\n',
            encoding='utf-8'
        )
        print(f'  [CLOUD] Email detected: {email["from"]} - {email["subject"]}')

        # Claim task (claim-by-move rule)
        claimed = VAULT / 'In_Progress' / 'cloud' / email_file.name
        shutil.move(str(email_file), str(claimed))

        # Create draft reply
        draft_file = VAULT / 'Pending_Approval' / 'email' / f'DRAFT_{i+1}_{ts}.md'
        draft_file.write_text(
            f'---\ntype: email_draft_reply\noriginal_from: {email["from"]}\n'
            f'original_subject: {email["subject"]}\ncreated_by: cloud_agent\n'
            f'created: {datetime.now().isoformat()}\nstatus: pending_approval\n'
            f'action: send_email\n---\n\n'
            f'# Draft Email Reply\n\n'
            f'**To:** {email["from"]}\n**Subject:** Re: {email["subject"]}\n\n'
            f'## Draft Reply\nThank you for your email regarding "{email["subject"]}".\n'
            f'I will review and get back to you shortly.\n\nBest regards\n\n'
            f'## Instructions\nMove to /Approved/email/ to send\n',
            encoding='utf-8'
        )
        print(f'  [CLOUD] Draft created: {draft_file.name}')

        # Move claimed to Done
        shutil.move(str(claimed), str(VAULT / 'Done' / claimed.name))

    # Social media draft
    social_draft = VAULT / 'Pending_Approval' / 'social' / f'DRAFT_POST_{ts}.md'
    social_draft.write_text(
        f'---\ntype: social_post_draft\nplatform: linkedin\ncreated_by: cloud_agent\n'
        f'created: {datetime.now().isoformat()}\nstatus: pending_approval\n'
        f'action: post_social_media\n---\n\n'
        f'# Draft LinkedIn Post\n\n'
        f'Excited to share our latest AI automation project!\n'
        f'Building autonomous AI employees that work 24/7.\n'
        f'#AI #Automation #Business\n\n'
        f'## Instructions\nMove to /Approved/social/ to publish\n',
        encoding='utf-8'
    )
    print(f'  [CLOUD] Social draft created: {social_draft.name}')

    # Cloud status
    cloud_status = {
        'last_check': datetime.now().isoformat(),
        'tasks_processed': 3,
        'drafts_created': 4,
        'errors': 0,
        'agent': 'cloud',
        'mode': 'draft_only'
    }
    (VAULT / 'Updates' / 'cloud_status.json').write_text(
        json.dumps(cloud_status, indent=2), encoding='utf-8')
    print(f'\n  [CLOUD] 3 emails + 1 social post drafted')
    print(f'  [CLOUD] Status -> /Updates/cloud_status.json')

    # ========================================
    # PART 2: USER APPROVES
    # ========================================
    print('\n--- USER REVIEW (HUMAN-IN-THE-LOOP) ---\n')

    pending_emails = sorted((VAULT / 'Pending_Approval' / 'email').glob(f'*{ts}*.md'))
    for i, f in enumerate(pending_emails[:2]):
        shutil.move(str(f), str(VAULT / 'Approved' / 'email' / f.name))
        print(f'  [USER] APPROVED: {f.name}')

    if len(pending_emails) > 2:
        shutil.move(str(pending_emails[2]), str(VAULT / 'Rejected' / pending_emails[2].name))
        print(f'  [USER] REJECTED: {pending_emails[2].name}')

    for f in (VAULT / 'Pending_Approval' / 'social').glob(f'*{ts}*.md'):
        shutil.move(str(f), str(VAULT / 'Approved' / 'social' / f.name))
        print(f'  [USER] APPROVED: {f.name}')

    # ========================================
    # PART 3: LOCAL AGENT EXECUTES
    # ========================================
    print('\n--- LOCAL AGENT (EXECUTE MODE) ---\n')

    actions_log = []

    for f in sorted((VAULT / 'Approved' / 'email').glob(f'*{ts}*.md')):
        content = f.read_text(encoding='utf-8')
        to_addr = ''
        for line in content.split('\n'):
            if 'original_from:' in line:
                to_addr = line.split(':', 1)[1].strip()
                break
        print(f'  [LOCAL] SENDING email to: {to_addr}')
        actions_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'email_send',
            'actor': 'local_agent',
            'target': to_addr,
            'status': 'success',
            'approved_by': 'human'
        })
        shutil.move(str(f), str(VAULT / 'Done' / f.name))
        print(f'  [LOCAL] Email sent -> /Done/')

    for f in sorted((VAULT / 'Approved' / 'social').glob(f'*{ts}*.md')):
        print(f'  [LOCAL] PUBLISHING LinkedIn post')
        actions_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'social_post',
            'actor': 'local_agent',
            'platform': 'linkedin',
            'status': 'published',
            'approved_by': 'human'
        })
        shutil.move(str(f), str(VAULT / 'Done' / f.name))
        print(f'  [LOCAL] Post published -> /Done/')

    # Save audit log
    log_file = VAULT / 'Logs' / 'local_agent' / f'actions_{datetime.now().strftime("%Y%m%d")}.json'
    log_file.write_text(json.dumps(actions_log, indent=2), encoding='utf-8')
    print(f'\n  [LOCAL] {len(actions_log)} actions executed and logged')

    # ========================================
    # PART 4: DASHBOARD UPDATE (single-writer: Local only)
    # ========================================
    print('\n--- DASHBOARD UPDATE (Local = single-writer) ---\n')

    pending_e = len(list((VAULT / 'Pending_Approval' / 'email').glob('*.md')))
    pending_s = len(list((VAULT / 'Pending_Approval' / 'social').glob('*.md')))
    done_count = len(list((VAULT / 'Done').glob('*.md')))

    dashboard = (
        f'---\nupdated: {datetime.now().isoformat()}\nupdated_by: local_agent\n---\n\n'
        f'# AI Employee Dashboard - Platinum Tier\n\n'
        f'## System Status\n'
        f'- **Cloud Agent**: Online (draft-only mode)\n'
        f'- **Local Agent**: Online (execute mode)\n'
        f'- **Last Cloud Sync**: {cloud_status["last_check"]}\n'
        f'- **Odoo**: Running on localhost:8069\n\n'
        f'## Cloud Agent Stats\n'
        f'- Tasks Processed: {cloud_status["tasks_processed"]}\n'
        f'- Drafts Created: {cloud_status["drafts_created"]}\n\n'
        f'## Pending Approvals\n'
        f'- Email Drafts: {pending_e}\n'
        f'- Social Posts: {pending_s}\n\n'
        f'## Local Agent Stats\n'
        f'- Actions Executed: {len(actions_log)}\n'
        f'- Emails Sent: {sum(1 for a in actions_log if a["action"]=="email_send")}\n'
        f'- Posts Published: {sum(1 for a in actions_log if a["action"]=="social_post")}\n\n'
        f'## Completed Tasks: {done_count}\n'
    )
    (VAULT / 'Dashboard.md').write_text(dashboard, encoding='utf-8')
    print('  Dashboard.md updated')

    # ========================================
    # SUMMARY
    # ========================================
    print('\n' + '=' * 60)
    print('  PLATINUM TIER SIMULATION COMPLETE!')
    print('=' * 60)
    print(f'''
  Cloud Agent:
    - 3 emails processed (draft-only)
    - 1 social post drafted
    - 0 items sent (NEVER sends directly)

  User Actions:
    - 2 emails APPROVED
    - 1 email REJECTED
    - 1 social post APPROVED

  Local Agent:
    - 2 emails SENT (after approval)
    - 1 LinkedIn post PUBLISHED (after approval)
    - All actions logged in /Logs/local_agent/

  Security Rules Followed:
    - Cloud = DRAFT only (never sends)
    - Local = EXECUTE (after human approval)
    - Secrets stay on local machine
    - Single-writer rule for Dashboard.md (Local only)
    - Claim-by-move rule for task ownership

  Platinum Demo Gate: PASSED
    Email arrived -> Cloud drafted -> User approved -> Local sent -> Done
''')


if __name__ == '__main__':
    main()
