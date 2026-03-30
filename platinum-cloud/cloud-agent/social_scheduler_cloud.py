#!/usr/bin/env python3
"""
Social Media Scheduler - Cloud Agent (Platinum Tier)

Runs on Cloud 24/7. Creates DRAFT social posts on schedule.
Does NOT publish - writes to /Pending_Approval/social/ for Local approval.
"""

import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
PENDING_SOCIAL = VAULT_PATH / 'Pending_Approval' / 'social'
LOGS = VAULT_PATH / 'Logs' / 'cloud_agent'

PENDING_SOCIAL.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [SocialScheduler] %(levelname)s: %(message)s')
logger = logging.getLogger('SocialScheduler')

# Schedule: posts to draft at these hours (24h format)
POST_SCHEDULE = [9, 14, 18]  # 9 AM, 2 PM, 6 PM

# Business topics for auto-generated posts
BUSINESS_TOPICS = [
    {
        'topic': 'AI Automation',
        'template': 'Exciting developments in AI-powered business automation! '
                     'Our team is building solutions that help businesses streamline operations 24/7. '
                     '#AI #Automation #Business #Innovation'
    },
    {
        'topic': 'Digital Transformation',
        'template': 'Digital transformation is not just about technology - '
                     'it is about reimagining how we work. AI employees can handle '
                     'routine tasks while humans focus on strategy and creativity. '
                     '#DigitalTransformation #FutureOfWork'
    },
    {
        'topic': 'Productivity',
        'template': 'How much time do you spend on repetitive tasks? '
                     'Our AI solutions automate email triage, social posting, '
                     'and accounting - saving 20+ hours per week. '
                     '#Productivity #TimeManagement #AIEmployee'
    },
    {
        'topic': 'Customer Service',
        'template': 'Fast response times = happy customers. '
                     'With AI-powered email and messaging automation, '
                     'your clients get responses within minutes, not hours. '
                     '#CustomerService #AI #BusinessGrowth'
    },
]


def create_draft_post(platform='linkedin'):
    """Create a draft social media post."""
    now = datetime.now()
    topic = BUSINESS_TOPICS[now.hour % len(BUSINESS_TOPICS)]
    ts = now.strftime('%Y%m%d_%H%M%S')

    draft_content = f"""---
type: social_post_draft
platform: {platform}
topic: {topic['topic']}
created_by: cloud_social_scheduler
created: {now.isoformat()}
scheduled_for: {now.strftime('%Y-%m-%d %H:00')}
status: pending_approval
action: post_social_media
---

# Draft Social Media Post

## Platform: {platform.title()}
## Topic: {topic['topic']}

## Content
{topic['template']}

## Instructions
- Review and edit this draft post
- Move to /Approved/social/ to publish
- Move to /Rejected/ to discard
- Edit the content above before approving if needed
"""

    draft_file = PENDING_SOCIAL / f'SCHEDULED_POST_{platform}_{ts}.md'
    draft_file.write_text(draft_content, encoding='utf-8')
    logger.info(f"Created draft post: {draft_file.name} (topic: {topic['topic']})")
    return draft_file


def should_post_now():
    """Check if current hour is in the schedule."""
    return datetime.now().hour in POST_SCHEDULE


def run():
    """Main scheduler loop."""
    logger.info("Starting Social Media Scheduler (Cloud Agent)...")
    logger.info(f"Schedule: {POST_SCHEDULE}")
    last_posted_hour = -1

    while True:
        now = datetime.now()

        if should_post_now() and now.hour != last_posted_hour:
            logger.info(f"Scheduled post time: {now.strftime('%H:%M')}")

            # Create LinkedIn draft
            create_draft_post('linkedin')

            # Create Facebook draft
            create_draft_post('facebook')

            last_posted_hour = now.hour

        time.sleep(300)  # Check every 5 minutes


if __name__ == '__main__':
    # For testing: create one draft immediately
    if '--test' in sys.argv:
        import sys
        create_draft_post('linkedin')
        create_draft_post('facebook')
        print("Test drafts created in /Pending_Approval/social/")
    else:
        run()
