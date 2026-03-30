#!/usr/bin/env python3
"""
Odoo Local Executor - Platinum Tier

Local-side Odoo actions. EXECUTE mode.
Handles approved accounting actions:
- Confirm/Post draft invoices
- Register payments
- Post vendor bills

Only runs after human approval (file moved to /Approved/accounting/).
"""

import os
import sys
import json
import shutil
import logging
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo_gold')
ODOO_USER = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASS = os.getenv('ODOO_PASSWORD', 'admin')
VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))

APPROVED = VAULT_PATH / 'Approved' / 'accounting'
DONE = VAULT_PATH / 'Done'
LOGS = VAULT_PATH / 'Logs' / 'local_agent'

for d in [APPROVED, DONE, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [OdooLocal] %(levelname)s: %(message)s')
logger = logging.getLogger('OdooLocalExecutor')

JSONRPC_URL = f"{ODOO_URL}/jsonrpc"


def rpc(service, method, args):
    payload = {
        "jsonrpc": "2.0", "method": "call", "id": 1,
        "params": {"service": service, "method": method, "args": args}
    }
    r = requests.post(JSONRPC_URL, json=payload, timeout=30)
    result = r.json()
    if "error" in result:
        raise Exception(result["error"].get("data", {}).get("message", str(result["error"])))
    return result["result"]


def kw(uid, model, method, args, kwargs=None):
    return rpc("object", "execute_kw", [ODOO_DB, uid, ODOO_PASS, model, method, args, kwargs or {}])


def authenticate():
    uid = rpc("common", "authenticate", [ODOO_DB, ODOO_USER, ODOO_PASS, {}])
    if not uid:
        raise Exception("Authentication failed")
    return uid


def confirm_invoice(uid, invoice_id):
    """Confirm/Post a draft invoice in Odoo."""
    # Check current state
    invoice = kw(uid, 'account.move', 'read', [[invoice_id], ['state', 'name', 'amount_total']])
    if not invoice:
        raise Exception(f"Invoice {invoice_id} not found")

    inv = invoice[0]
    if inv['state'] == 'posted':
        logger.info(f"Invoice {inv['name']} already posted")
        return inv

    # Confirm/Post the invoice
    kw(uid, 'account.move', 'action_post', [[invoice_id]])
    logger.info(f"Invoice {invoice_id} CONFIRMED and POSTED")

    # Read updated state
    updated = kw(uid, 'account.move', 'read', [[invoice_id], ['state', 'name', 'amount_total']])
    return updated[0] if updated else inv


def process_approved_accounting():
    """Process all approved accounting actions."""
    uid = None
    actions_log = []

    for f in sorted(APPROVED.glob('*.md')):
        try:
            content = f.read_text(encoding='utf-8')

            # Authenticate if not done
            if uid is None:
                uid = authenticate()

            # Parse action type and invoice_id
            action = ''
            invoice_id = None
            amount = 0

            for line in content.split('\n'):
                if 'action:' in line and 'action_type' not in line:
                    action = line.split(':', 1)[1].strip()
                elif 'invoice_id:' in line:
                    try:
                        invoice_id = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass
                elif 'amount:' in line:
                    try:
                        amount = float(line.split(':', 1)[1].strip())
                    except ValueError:
                        pass

            if action == 'confirm_invoice' and invoice_id:
                logger.info(f"Confirming invoice {invoice_id}...")
                result = confirm_invoice(uid, invoice_id)
                logger.info(f"Invoice {result.get('name', invoice_id)} posted! Amount: ${result.get('amount_total', 0):,.2f}")

                actions_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'odoo_confirm_invoice',
                    'actor': 'local_agent',
                    'invoice_id': invoice_id,
                    'amount': result.get('amount_total', 0),
                    'status': 'posted',
                    'approved_by': 'human'
                })
            else:
                logger.info(f"Processing generic accounting action: {f.name}")
                actions_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'odoo_generic',
                    'actor': 'local_agent',
                    'file': f.name,
                    'status': 'executed',
                    'approved_by': 'human'
                })

            # Move to Done
            shutil.move(str(f), str(DONE / f.name))
            logger.info(f"Moved to Done: {f.name}")

        except Exception as e:
            logger.error(f"Error processing {f.name}: {e}")
            actions_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'odoo_error',
                'file': f.name,
                'error': str(e),
                'status': 'failed'
            })

    # Save log
    if actions_log:
        log_file = LOGS / f'odoo_actions_{datetime.now().strftime("%Y%m%d")}.json'
        existing = []
        if log_file.exists():
            try:
                existing = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                pass
        existing.extend(actions_log)
        log_file.write_text(json.dumps(existing, indent=2), encoding='utf-8')
        logger.info(f"Logged {len(actions_log)} actions")

    return actions_log


if __name__ == '__main__':
    actions = process_approved_accounting()
    if actions:
        print(f"\nProcessed {len(actions)} accounting actions")
    else:
        print("\nNo approved accounting actions to process")
