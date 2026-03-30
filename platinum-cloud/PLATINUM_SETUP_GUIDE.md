# Platinum Tier: Cloud + Local Setup Guide

## Architecture

```
┌─────────────────────────┐    Git Sync     ┌─────────────────────────┐
│   ORACLE CLOUD VM       │ ←────────────→  │   LOCAL LAPTOP          │
│   (Always-On 24/7)      │  (vault files)  │   (When you're online)  │
│                         │                 │                         │
│   Cloud Agent:          │                 │   Local Agent:          │
│   - Gmail Watcher       │                 │   - WhatsApp Watcher    │
│   - LinkedIn Watcher    │                 │   - Approval Workflow   │
│   - Social Post Drafts  │                 │   - Final Send Actions  │
│   - Odoo (24/7)         │                 │   - Banking/Payments    │
│   - Email Draft Replies │                 │   - Dashboard.md writer │
│                         │                 │                         │
│   DRAFT-ONLY mode       │                 │   EXECUTE mode          │
│   (never sends directly)│                 │   (after approval)      │
└─────────────────────────┘                 └─────────────────────────┘
```

## Oracle Cloud Free Tier Setup

### 1. Create Account
- Go to: https://www.oracle.com/cloud/free/
- Sign up (credit card required but NOT charged)



### 2. Create VM
- Shape: VM.Standard.A1.Flex (ARM - Always Free)
- OCPUs: 2
- Memory: 12 GB
- OS: Ubuntu 22.04
- Boot Volume: 50 GB

### 3. SSH Access
```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oracle_cloud

# Connect to VM
ssh -i ~/.ssh/oracle_cloud ubuntu@<VM_PUBLIC_IP>
```

### 4. Run Cloud Setup Script
```bash
# On the VM:
git clone <your-repo-url> ~/ai-employee
cd ~/ai-employee/platinum-cloud
chmod +x scripts/cloud_vm_setup.sh
./scripts/cloud_vm_setup.sh
```

### 5. Configure Vault Sync
```bash
# On the VM:
cd ~/ai-employee
git remote add origin <your-repo-url>
crontab -e
# Add: */5 * * * * cd ~/ai-employee && git pull --rebase && git add -A && git commit -m "cloud-sync" && git push
```

### 6. Start Cloud Agent
```bash
pm2 start cloud-agent/cloud_orchestrator.py --interpreter python3
pm2 start cloud-agent/gmail_watcher_cloud.py --interpreter python3
pm2 save
pm2 startup
```

## Security Rules
- .env NEVER syncs (in .gitignore)
- WhatsApp sessions stay LOCAL only
- Banking credentials stay LOCAL only
- Cloud has its own .env with ONLY: Gmail API, LinkedIn API, Odoo URL

## Platinum Demo Flow
1. Email arrives → Cloud Gmail Watcher detects
2. Cloud drafts reply → writes to /Pending_Approval/email/
3. Git sync → file appears on Local
4. User approves → moves to /Approved/
5. Local agent sends email via MCP
6. File moves to /Done/
7. Logs updated
