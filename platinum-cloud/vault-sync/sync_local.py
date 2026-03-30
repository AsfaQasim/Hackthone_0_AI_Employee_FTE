#!/usr/bin/env python3
"""
Vault Sync - Local Side (Platinum Tier)

Syncs the vault between Local and Cloud via Git.
Runs periodically to pull cloud changes and push local changes.

Security: .env, sessions, banking creds are in .gitignore - NEVER sync.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path(os.getenv('VAULT_PATH', 'F:/hackthone_0'))
SYNC_INTERVAL = 120  # 2 minutes
LOGS = VAULT_PATH / 'Logs' / 'vault_sync'
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [VaultSync] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS / f'sync_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VaultSync')


def run_git(args, cwd=None):
    """Run a git command and return output."""
    cmd = ['git'] + args
    result = subprocess.run(cmd, cwd=str(cwd or VAULT_PATH),
                          capture_output=True, text=True, timeout=30)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def sync():
    """Pull cloud changes, push local changes."""
    try:
        # Pull cloud changes
        code, out, err = run_git(['pull', '--rebase', 'origin', 'main'])
        if code == 0:
            if 'Already up to date' not in out:
                logger.info(f"Pulled cloud changes: {out}")
        else:
            logger.warning(f"Pull issue: {err}")
            # Try to resolve conflicts
            run_git(['rebase', '--abort'])
            run_git(['pull', 'origin', 'main', '--no-rebase'])

        # Stage local changes
        run_git(['add', '-A'])

        # Check if there are changes to commit
        code, out, _ = run_git(['diff', '--cached', '--quiet'])
        if code != 0:
            # There are changes
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            run_git(['commit', '-m', f'local-sync {timestamp}'])

            # Push to remote
            code, out, err = run_git(['push', 'origin', 'main'])
            if code == 0:
                logger.info(f"Pushed local changes")
            else:
                logger.warning(f"Push issue: {err}")

    except subprocess.TimeoutExpired:
        logger.error("Git operation timed out")
    except Exception as e:
        logger.error(f"Sync error: {e}")


def main():
    logger.info(f"Starting Vault Sync (interval: {SYNC_INTERVAL}s)")
    logger.info(f"Vault path: {VAULT_PATH}")

    while True:
        sync()
        time.sleep(SYNC_INTERVAL)


if __name__ == '__main__':
    main()
