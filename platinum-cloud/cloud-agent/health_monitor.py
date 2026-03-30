#!/usr/bin/env python3
"""
Health Monitor - Cloud VM (Platinum Tier)

Monitors all cloud services and restarts if needed.
Runs via PM2 on the Cloud VM.
"""

import os
import time
import json
import logging
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))
LOGS = VAULT_PATH / 'Logs' / 'cloud_agent'
LOGS.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [HealthMonitor] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOGS / f'health_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('HealthMonitor')

CHECK_INTERVAL = 60  # seconds


def check_odoo():
    """Check if Odoo is running."""
    try:
        resp = requests.get('http://localhost:8069/web/database/selector', timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def check_cloud_orchestrator():
    """Check if Cloud Orchestrator is healthy."""
    try:
        resp = requests.get('http://localhost:8080/health', timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def check_pm2_processes():
    """Check PM2 managed processes."""
    try:
        result = subprocess.run(['pm2', 'jlist'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            processes = json.loads(result.stdout)
            return {p['name']: p['pm2_env']['status'] for p in processes}
    except Exception:
        pass
    return {}


def restart_service(name):
    """Restart a PM2 service."""
    try:
        subprocess.run(['pm2', 'restart', name], capture_output=True, timeout=30)
        logger.info(f"Restarted service: {name}")
    except Exception as e:
        logger.error(f"Failed to restart {name}: {e}")


def check_docker_containers():
    """Check Docker containers status."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}:{{.Status}}'],
            capture_output=True, text=True, timeout=10
        )
        containers = {}
        for line in result.stdout.strip().split('\n'):
            if ':' in line:
                name, status = line.split(':', 1)
                containers[name] = 'Up' in status
        return containers
    except Exception:
        return {}


def write_health_report(checks):
    """Write health report to vault."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'checks': checks,
        'overall': all(v for v in checks.values() if isinstance(v, bool))
    }

    report_file = LOGS / 'health_latest.json'
    report_file.write_text(json.dumps(report, indent=2))

    # Also write markdown for vault
    md_content = f"""---
type: health_report
timestamp: {datetime.now().isoformat()}
status: {'healthy' if report['overall'] else 'ISSUES DETECTED'}
---

# Cloud Health Report

**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** {'All Systems Healthy' if report['overall'] else 'ISSUES DETECTED'}

## Service Status
"""
    for service, status in checks.items():
        icon = 'OK' if status else 'FAIL'
        md_content += f"- **{service}**: {icon}\n"

    health_md = VAULT_PATH / 'Updates' / 'cloud_health.md'
    health_md.parent.mkdir(parents=True, exist_ok=True)
    health_md.write_text(md_content, encoding='utf-8')


def main():
    logger.info("Starting Health Monitor...")

    while True:
        checks = {}

        # Check Odoo
        checks['odoo'] = check_odoo()
        if not checks['odoo']:
            logger.warning("Odoo is down! Attempting restart...")
            subprocess.run(['docker', 'compose', '-f',
                          str(VAULT_PATH / 'odoo-gold' / 'docker-compose.yml'),
                          'up', '-d'], capture_output=True)

        # Check Cloud Orchestrator
        checks['cloud_orchestrator'] = check_cloud_orchestrator()
        if not checks['cloud_orchestrator']:
            logger.warning("Cloud Orchestrator is down!")
            restart_service('cloud_orchestrator')

        # Check Docker containers
        containers = check_docker_containers()
        for name, running in containers.items():
            checks[f'docker_{name}'] = running

        # Check PM2 processes
        pm2_procs = check_pm2_processes()
        for name, status in pm2_procs.items():
            checks[f'pm2_{name}'] = status == 'online'

        # Write report
        write_health_report(checks)

        overall = all(v for v in checks.values() if isinstance(v, bool))
        if overall:
            logger.info("All systems healthy")
        else:
            failed = [k for k, v in checks.items() if isinstance(v, bool) and not v]
            logger.warning(f"Issues detected: {failed}")

        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    main()
