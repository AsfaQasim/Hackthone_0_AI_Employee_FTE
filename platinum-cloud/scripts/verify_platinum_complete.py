#!/usr/bin/env python3
"""
Platinum Tier - Complete Verification Script

Checks ALL Platinum requirements are met.
"""

import os
import sys
from pathlib import Path

VAULT = Path('F:/hackthone_0')

passed = 0
failed = 0


def check(name, condition):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name}")
        failed += 1
    return condition


def file_exists(path):
    return (VAULT / path).exists()


def dir_exists(path):
    return (VAULT / path).is_dir()


def main():
    global passed, failed

    print("=" * 60)
    print("  PLATINUM TIER - COMPLETE VERIFICATION")
    print("=" * 60)

    # 1. Cloud VM 24/7 (scripts)
    print("\n[1/7] Cloud VM 24/7 - Always-on watchers + orchestrator + health")
    check("Cloud VM setup script", file_exists("platinum-cloud/scripts/cloud_vm_setup.sh"))
    check("Cloud orchestrator", file_exists("platinum-cloud/cloud-agent/cloud_orchestrator.py"))
    check("Cloud Gmail watcher", file_exists("platinum-cloud/cloud-agent/gmail_watcher_cloud.py"))
    check("Health monitor", file_exists("platinum-cloud/cloud-agent/health_monitor.py"))
    check("Social scheduler", file_exists("platinum-cloud/cloud-agent/social_scheduler_cloud.py"))
    check("Odoo cloud agent", file_exists("platinum-cloud/cloud-agent/odoo_cloud_agent.py"))
    check("PM2 process management (in setup script)",
          "pm2" in (VAULT / "platinum-cloud/scripts/cloud_vm_setup.sh").read_text())
    check(".env.cloud template", file_exists("platinum-cloud/scripts/.env.cloud"))

    # 2. Work-Zone Specialization
    print("\n[2/7] Work-Zone Specialization (Cloud=draft, Local=execute)")
    check("Cloud orchestrator is DRAFT_ONLY",
          "DRAFT_ONLY" in (VAULT / "platinum-cloud/cloud-agent/cloud_orchestrator.py").read_text())
    check("Local orchestrator EXECUTES",
          "EXECUTE" in (VAULT / "platinum-cloud/local-agent/local_orchestrator.py").read_text() or
          "process_approved" in (VAULT / "platinum-cloud/local-agent/local_orchestrator.py").read_text())
    check("Cloud owns email drafts",
          "process_email_task" in (VAULT / "platinum-cloud/cloud-agent/cloud_orchestrator.py").read_text())
    check("Cloud owns social drafts",
          "process_social_task" in (VAULT / "platinum-cloud/cloud-agent/cloud_orchestrator.py").read_text())
    check("Local owns WhatsApp",
          file_exists("platinum-cloud/local-agent/whatsapp_local_handler.py"))
    check("Local owns Odoo execution",
          file_exists("platinum-cloud/local-agent/odoo_local_executor.py"))

    # 3. Delegation via Synced Vault
    print("\n[3/7] Delegation via Synced Vault (Phase 1)")
    check("/Needs_Action/email/", dir_exists("Needs_Action/email"))
    check("/Needs_Action/social/", dir_exists("Needs_Action/social"))
    check("/Needs_Action/accounting/", dir_exists("Needs_Action/accounting"))
    check("/Plans/email/", dir_exists("Plans/email"))
    check("/Plans/social/", dir_exists("Plans/social"))
    check("/Plans/accounting/", dir_exists("Plans/accounting"))
    check("/Pending_Approval/email/", dir_exists("Pending_Approval/email"))
    check("/Pending_Approval/social/", dir_exists("Pending_Approval/social"))
    check("/Pending_Approval/accounting/", dir_exists("Pending_Approval/accounting"))
    check("/In_Progress/cloud/", dir_exists("In_Progress/cloud"))
    check("/In_Progress/local/", dir_exists("In_Progress/local"))
    check("/Updates/ folder", dir_exists("Updates"))
    check("/Signals/ folder", dir_exists("Signals"))
    check("Claim-by-move rule in orchestrator",
          "claim_task" in (VAULT / "platinum-cloud/cloud-agent/cloud_orchestrator.py").read_text())
    check("Single-writer Dashboard.md (Local only)",
          "merge_cloud_updates" in (VAULT / "platinum-cloud/local-agent/local_orchestrator.py").read_text())
    check("Git vault sync script", file_exists("platinum-cloud/vault-sync/sync_local.py"))

    # 4. Security Rules
    print("\n[4/7] Security - Secrets never sync")
    gitignore = (VAULT / ".gitignore").read_text()
    check(".env in .gitignore", ".env" in gitignore)
    check("WhatsApp session in .gitignore", "whatsapp_session" in gitignore.lower() or "_session" in gitignore)
    check("Token files in .gitignore", "token" in gitignore.lower())
    check("Credentials in .gitignore", "credentials" in gitignore.lower())
    check("Cloud .env.cloud has DRAFT_ONLY=true",
          "DRAFT_ONLY=true" in (VAULT / "platinum-cloud/scripts/.env.cloud").read_text())
    check("WhatsApp handler marked local_only",
          "local_only" in (VAULT / "platinum-cloud/local-agent/whatsapp_local_handler.py").read_text() or
          "NEVER" in (VAULT / "platinum-cloud/local-agent/whatsapp_local_handler.py").read_text())

    # 5. Odoo on Cloud with HTTPS, backups, health
    print("\n[5/7] Odoo Cloud Deployment (HTTPS + backups + health)")
    check("Odoo docker-compose (local)", file_exists("odoo-gold/docker-compose.yml"))
    check("Odoo docker-compose (cloud with nginx)", file_exists("odoo-gold/docker-compose.cloud.yml"))
    check("Nginx HTTPS config", file_exists("odoo-gold/nginx.conf"))
    check("Nginx has SSL config",
          "ssl_certificate" in (VAULT / "odoo-gold/nginx.conf").read_text())
    check("Odoo backup script", file_exists("odoo-gold/backup_odoo.py"))
    check("Backup has retention policy",
          "KEEP_DAILY" in (VAULT / "odoo-gold/backup_odoo.py").read_text())
    check("Odoo health check in health_monitor",
          "check_odoo" in (VAULT / "platinum-cloud/cloud-agent/health_monitor.py").read_text())
    check("Cloud Odoo agent (draft-only)",
          file_exists("platinum-cloud/cloud-agent/odoo_cloud_agent.py"))
    check("Odoo draft invoices require approval",
          "pending_approval" in (VAULT / "platinum-cloud/cloud-agent/odoo_cloud_agent.py").read_text())
    check("Local Odoo executor (confirm invoices)",
          "confirm_invoice" in (VAULT / "platinum-cloud/local-agent/odoo_local_executor.py").read_text())

    # 6. Optional A2A Upgrade
    print("\n[6/7] A2A Upgrade (Phase 2 - Optional)")
    check("A2A messaging module", file_exists("platinum-cloud/a2a_messaging.py"))
    a2a_content = (VAULT / "platinum-cloud/a2a_messaging.py").read_text()
    check("A2A message types defined", "approval_request" in a2a_content)
    check("A2A HTTP server", "HTTPServer" in a2a_content)
    check("A2A vault audit record", "signal_file" in a2a_content or "Signals" in a2a_content)

    # 7. Platinum Demo
    print("\n[7/7] Platinum Demo (minimum passing gate)")
    check("Platinum demo script", file_exists("platinum-cloud/scripts/platinum_demo.py"))
    check("Full simulation script", file_exists("platinum-cloud/scripts/platinum_full_simulation.py"))
    check("Done folder has completed tasks", len(list((VAULT / "Done").glob("*.md"))) > 0)
    check("Logs exist", len(list((VAULT / "Logs").rglob("*.json"))) > 0)
    check("Cloud status in Updates", file_exists("Updates/cloud_status.json"))

    # Summary
    total = passed + failed
    print("\n" + "=" * 60)
    print(f"  RESULTS: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("  STATUS: ALL PLATINUM REQUIREMENTS COMPLETE!")
        print("\n  Ready for:")
        print("    - Deploy to Oracle Cloud VM when account is ready")
        print("    - Demo video recording")
        print("    - Hackathon submission")
    else:
        print("  STATUS: SOME REQUIREMENTS MISSING")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
