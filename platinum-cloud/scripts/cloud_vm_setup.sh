#!/bin/bash
# ============================================
# Oracle Cloud VM Setup Script
# Platinum Tier - AI Employee Cloud Agent
# ============================================

set -e

echo "============================================"
echo "  AI Employee - Cloud VM Setup"
echo "  Platinum Tier"
echo "============================================"

# Step 1: System Update
echo ""
echo "[1/8] Updating system..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Python
echo ""
echo "[2/8] Installing Python 3.12+..."
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Step 3: Install Node.js (for PM2)
echo ""
echo "[3/8] Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Step 4: Install PM2 (Process Manager)
echo ""
echo "[4/8] Installing PM2..."
sudo npm install -g pm2

# Step 5: Install Docker & Docker Compose (for Odoo)
echo ""
echo "[5/8] Installing Docker..."
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Step 6: Setup Python Virtual Environment
echo ""
echo "[6/8] Setting up Python environment..."
cd ~/ai-employee
python3 -m venv venv
source venv/bin/activate
pip install requests python-dotenv google-auth google-auth-oauthlib google-api-python-client playwright

# Step 7: Create vault directories
echo ""
echo "[7/8] Creating vault directories..."
mkdir -p Needs_Action/email Needs_Action/social Needs_Action/accounting
mkdir -p Pending_Approval/email Pending_Approval/social Pending_Approval/accounting
mkdir -p In_Progress/cloud In_Progress/local
mkdir -p Plans/email Plans/social Plans/accounting
mkdir -p Updates
mkdir -p Done
mkdir -p Logs/cloud_agent

# Step 8: Setup Git sync cron
echo ""
echo "[8/8] Setting up Git sync..."
cat > ~/sync_vault.sh << 'SYNC_EOF'
#!/bin/bash
cd ~/ai-employee
git pull --rebase origin main 2>/dev/null
git add -A
git diff --cached --quiet || git commit -m "cloud-agent-sync $(date +%Y%m%d_%H%M%S)"
git push origin main 2>/dev/null
SYNC_EOF

chmod +x ~/sync_vault.sh

# Add to crontab (every 2 minutes)
(crontab -l 2>/dev/null; echo "*/2 * * * * /home/$USER/sync_vault.sh >> /home/$USER/ai-employee/Logs/cloud_agent/git_sync.log 2>&1") | crontab -

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Copy .env.cloud to .env and fill in credentials"
echo "  2. Start Odoo:  cd odoo-gold && docker compose up -d"
echo "  3. Run Odoo setup: python odoo-gold/setup_odoo.py"
echo "  4. Start Cloud Agent: pm2 start platinum-cloud/cloud-agent/cloud_orchestrator.py --interpreter python3"
echo "  5. Save PM2: pm2 save && pm2 startup"
echo ""
echo "NOTE: Log out and log back in for Docker group to take effect"
