#!/usr/bin/env python3
"""
Odoo Cloud Agent - Platinum Tier

Cloud-side Odoo integration. DRAFT-ONLY mode.
- Can READ Odoo data (invoices, customers, reports)
- Can create DRAFT invoices/bills (not posted)
- Cannot POST/CONFIRM invoices (requires Local approval)
- Cannot make payments (requires Local approval)

Local Agent handles: confirm invoice, register payment, post entries
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo_gold')
ODOO_USER = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASS = os.getenv('ODOO_PASSWORD', 'admin')
VAULT_PATH = Path(os.getenv('VAULT_PATH', '.'))

PENDING_APPROVAL = VAULT_PATH / 'Pending_Approval' / 'accounting'
UPDATES = VAULT_PATH / 'Updates'
LOGS = VAULT_PATH / 'Logs' / 'cloud_agent'

for d in [PENDING_APPROVAL, UPDATES, LOGS]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [OdooCloud] %(levelname)s: %(message)s')
logger = logging.getLogger('OdooCloudAgent')

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
        raise Exception("Odoo authentication failed")
    return uid


def create_draft_invoice(uid, partner_name, lines):
    """
    Create a DRAFT invoice in Odoo. Does NOT confirm/post it.
    Writes approval request for Local to confirm.
    """
    # Find or create partner
    partners = kw(uid, 'res.partner', 'search_read',
                  [[('name', 'ilike', partner_name)]],
                  {'fields': ['id', 'name'], 'limit': 1})

    if partners:
        partner_id = partners[0]['id']
    else:
        partner_id = kw(uid, 'res.partner', 'create', [{'name': partner_name, 'customer_rank': 1}])

    # Create draft invoice
    invoice_lines = [(0, 0, {
        'name': line['name'],
        'quantity': line.get('quantity', 1),
        'price_unit': line['price']
    }) for line in lines]

    invoice_id = kw(uid, 'account.move', 'create', [{
        'move_type': 'out_invoice',
        'partner_id': partner_id,
        'invoice_date': datetime.now().strftime('%Y-%m-%d'),
        'invoice_line_ids': invoice_lines
    }])

    # Read back the invoice
    invoice = kw(uid, 'account.move', 'read', [[invoice_id],
                 ['name', 'amount_total', 'state']])

    total = invoice[0]['amount_total'] if invoice else 0

    # Write approval request - Local must CONFIRM this invoice
    approval_file = PENDING_APPROVAL / f'ODOO_INVOICE_{invoice_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    approval_file.write_text(f"""---
type: odoo_invoice_approval
action: confirm_invoice
invoice_id: {invoice_id}
partner: {partner_name}
amount: {total}
created_by: cloud_agent
created: {datetime.now().isoformat()}
status: pending_approval
---

# Odoo Invoice - Pending Approval

**Invoice ID:** {invoice_id}
**Customer:** {partner_name}
**Amount:** ${total:,.2f}
**Status:** DRAFT (not yet posted)

## Line Items
{chr(10).join(f'- {l["name"]}: {l.get("quantity",1)} x ${l["price"]:,.2f}' for l in lines)}

## Required Action
This invoice was created as DRAFT by Cloud Agent.
To CONFIRM and POST this invoice:
- Move this file to /Approved/accounting/

To CANCEL:
- Move this file to /Rejected/
""", encoding='utf-8')

    logger.info(f"Draft invoice created: ID={invoice_id}, Amount=${total:,.2f}")
    return invoice_id


def get_accounting_summary(uid):
    """Get accounting summary and write to Updates for Local dashboard."""
    now = datetime.now()
    month_start = now.replace(day=1).strftime('%Y-%m-%d')

    # Revenue (customer invoices)
    invoices = kw(uid, 'account.move', 'search_read', [
        [('move_type', '=', 'out_invoice'), ('invoice_date', '>=', month_start)]
    ], {'fields': ['amount_total', 'state', 'payment_state', 'partner_id']})

    revenue_total = sum(i['amount_total'] for i in invoices)
    revenue_posted = sum(i['amount_total'] for i in invoices if i['state'] == 'posted')
    revenue_draft = sum(i['amount_total'] for i in invoices if i['state'] == 'draft')
    revenue_paid = sum(i['amount_total'] for i in invoices if i.get('payment_state') == 'paid')

    # Expenses (vendor bills)
    bills = kw(uid, 'account.move', 'search_read', [
        [('move_type', '=', 'in_invoice'), ('invoice_date', '>=', month_start)]
    ], {'fields': ['amount_total', 'state', 'payment_state']})

    expenses_total = sum(b['amount_total'] for b in bills)

    summary = {
        'timestamp': now.isoformat(),
        'period': f'{month_start} to {now.strftime("%Y-%m-%d")}',
        'revenue': {
            'total': revenue_total,
            'posted': revenue_posted,
            'draft': revenue_draft,
            'paid': revenue_paid,
            'pending': revenue_total - revenue_paid,
            'invoice_count': len(invoices)
        },
        'expenses': {
            'total': expenses_total,
            'bill_count': len(bills)
        },
        'profit': revenue_posted - expenses_total,
        'generated_by': 'cloud_odoo_agent'
    }

    # Write to Updates
    (UPDATES / 'odoo_accounting_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')

    logger.info(f"Accounting summary: Revenue=${revenue_total:,.2f}, Expenses=${expenses_total:,.2f}")
    return summary


def check_overdue_invoices(uid):
    """Check for overdue unpaid invoices and create alerts."""
    overdue = kw(uid, 'account.move', 'search_read', [
        [('move_type', '=', 'out_invoice'),
         ('state', '=', 'posted'),
         ('payment_state', '!=', 'paid'),
         ('invoice_date_due', '<', datetime.now().strftime('%Y-%m-%d'))]
    ], {'fields': ['name', 'partner_id', 'amount_total', 'invoice_date_due']})

    if overdue:
        alert_file = UPDATES / 'odoo_overdue_alert.md'
        lines = [f"---\ntype: odoo_alert\ntimestamp: {datetime.now().isoformat()}\n---\n",
                 "# Overdue Invoice Alert\n"]
        for inv in overdue:
            partner = inv['partner_id'][1] if inv['partner_id'] else 'Unknown'
            lines.append(f"- **{inv['name']}**: ${inv['amount_total']:,.2f} from {partner} (due: {inv['invoice_date_due']})")

        alert_file.write_text('\n'.join(lines), encoding='utf-8')
        logger.warning(f"{len(overdue)} overdue invoices detected!")

    return overdue


def run_periodic():
    """Run periodic Odoo cloud tasks."""
    logger.info("Starting Odoo Cloud Agent periodic tasks...")

    try:
        uid = authenticate()
        logger.info(f"Authenticated with Odoo (UID: {uid})")

        # Get accounting summary
        get_accounting_summary(uid)

        # Check overdue invoices
        check_overdue_invoices(uid)

        logger.info("Periodic tasks completed")

    except Exception as e:
        logger.error(f"Odoo Cloud Agent error: {e}")


if __name__ == '__main__':
    run_periodic()
