#!/usr/bin/env python3
"""
Odoo Backup Script - Platinum Tier

Automated backups for Odoo database.
Runs via cron/PM2 on Cloud VM.
Keeps last 7 daily backups + last 4 weekly backups.
"""

import os
import sys
import time
import json
import shutil
import logging
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo_gold')
ODOO_MASTER_PASSWORD = os.getenv('ODOO_MASTER_PASSWORD', 'admin_master_2026')
BACKUP_DIR = Path(os.getenv('BACKUP_DIR', './odoo-gold/backups'))
KEEP_DAILY = 7
KEEP_WEEKLY = 4

BACKUP_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [OdooBackup] %(levelname)s: %(message)s'
)
logger = logging.getLogger('OdooBackup')


def backup_database():
    """Create Odoo database backup via web endpoint."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = BACKUP_DIR / f'odoo_backup_{ODOO_DB}_{timestamp}.zip'

    logger.info(f"Starting backup of database '{ODOO_DB}'...")

    try:
        # Method 1: Odoo web backup endpoint
        resp = requests.post(
            f'{ODOO_URL}/web/database/backup',
            data={
                'master_pwd': ODOO_MASTER_PASSWORD,
                'name': ODOO_DB,
                'backup_format': 'zip'
            },
            stream=True,
            timeout=300
        )

        if resp.status_code == 200 and 'application/octet-stream' in resp.headers.get('Content-Type', ''):
            with open(backup_file, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = backup_file.stat().st_size / (1024 * 1024)
            logger.info(f"Backup created: {backup_file.name} ({size_mb:.1f} MB)")
            return backup_file
        else:
            logger.warning(f"Web backup returned status {resp.status_code}, trying pg_dump...")
            raise Exception("Web backup failed")

    except Exception as e:
        logger.warning(f"Web backup failed ({e}), trying pg_dump method...")

        # Method 2: Direct pg_dump via Docker
        try:
            dump_file = BACKUP_DIR / f'odoo_backup_{ODOO_DB}_{timestamp}.sql'
            result = subprocess.run([
                'docker', 'exec', 'odoo_gold_db',
                'pg_dump', '-U', 'odoo', ODOO_DB
            ], capture_output=True, timeout=300)

            if result.returncode == 0:
                dump_file.write_bytes(result.stdout)
                size_mb = dump_file.stat().st_size / (1024 * 1024)
                logger.info(f"Backup created (pg_dump): {dump_file.name} ({size_mb:.1f} MB)")
                return dump_file
            else:
                logger.error(f"pg_dump failed: {result.stderr.decode()}")
                return None

        except Exception as e2:
            logger.error(f"Both backup methods failed: {e2}")
            return None


def cleanup_old_backups():
    """Remove old backups keeping KEEP_DAILY daily + KEEP_WEEKLY weekly."""
    all_backups = sorted(BACKUP_DIR.glob('odoo_backup_*'), key=lambda f: f.stat().st_mtime, reverse=True)

    if len(all_backups) <= KEEP_DAILY:
        return

    now = datetime.now()
    to_keep = set()

    # Keep last N daily
    for f in all_backups[:KEEP_DAILY]:
        to_keep.add(f)

    # Keep weekly backups (one per week for last KEEP_WEEKLY weeks)
    for week in range(KEEP_WEEKLY):
        week_start = now - timedelta(days=7 * (week + 1))
        week_end = now - timedelta(days=7 * week)
        for f in all_backups:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if week_start <= mtime < week_end:
                to_keep.add(f)
                break

    # Remove files not in keep list
    removed = 0
    for f in all_backups:
        if f not in to_keep:
            f.unlink()
            removed += 1

    if removed:
        logger.info(f"Cleaned up {removed} old backups. Keeping {len(to_keep)}.")


def write_backup_status(backup_file):
    """Write backup status to vault for monitoring."""
    status = {
        'last_backup': datetime.now().isoformat(),
        'file': str(backup_file) if backup_file else None,
        'size_bytes': backup_file.stat().st_size if backup_file else 0,
        'success': backup_file is not None,
        'database': ODOO_DB,
        'backups_count': len(list(BACKUP_DIR.glob('odoo_backup_*')))
    }

    status_file = BACKUP_DIR / 'backup_status.json'
    status_file.write_text(json.dumps(status, indent=2))

    # Also write to Updates for vault sync
    updates_dir = Path(os.getenv('VAULT_PATH', '.')) / 'Updates'
    updates_dir.mkdir(parents=True, exist_ok=True)
    (updates_dir / 'odoo_backup_status.json').write_text(json.dumps(status, indent=2))


def main():
    logger.info("=" * 50)
    logger.info("Odoo Backup - Starting")
    logger.info("=" * 50)

    # Create backup
    backup_file = backup_database()

    # Cleanup old backups
    cleanup_old_backups()

    # Write status
    write_backup_status(backup_file)

    if backup_file:
        logger.info("Backup completed successfully!")
    else:
        logger.error("Backup FAILED!")

    return 0 if backup_file else 1


if __name__ == '__main__':
    sys.exit(main())
