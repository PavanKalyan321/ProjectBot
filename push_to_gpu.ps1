# Push all files to GPU server
$DROPLET_IP = "142.93.158.30"
$SSH_KEY = "C:\Project\aviator_key"
$LOCAL_PROJECT = "C:\Project"
$REMOTE_PATH = "/root/aviator-bot"

Write-Host "========================================" -ForegroundColor Green
Write-Host "Pushing files to GPU server" -ForegroundColor Green
Write-Host "Server: $DROPLET_IP" -ForegroundColor Green
Write-Host "Remote Path: $REMOTE_PATH" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Create remote directory
Write-Host "Creating remote directory..." -ForegroundColor Yellow
ssh -i $SSH_KEY root@$DROPLET_IP "mkdir -p $REMOTE_PATH"

# Copy all files using SCP
Write-Host "Copying project files..." -ForegroundColor Yellow
scp -i $SSH_KEY -r "$LOCAL_PROJECT\backend" "root@${DROPLET_IP}:${REMOTE_PATH}/"
scp -i $SSH_KEY -r "$LOCAL_PROJECT\templates" "root@${DROPLET_IP}:${REMOTE_PATH}/" 2>$null
scp -i $SSH_KEY -r "$LOCAL_PROJECT\scripts" "root@${DROPLET_IP}:${REMOTE_PATH}/" 2>$null
scp -i $SSH_KEY "$LOCAL_PROJECT\requirements.txt" "root@${DROPLET_IP}:${REMOTE_PATH}/"
scp -i $SSH_KEY "$LOCAL_PROJECT\README.md" "root@${DROPLET_IP}:${REMOTE_PATH}/" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Files pushed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Verify files
Write-Host "Verifying files on server..." -ForegroundColor Yellow
ssh -i $SSH_KEY root@$DROPLET_IP "ls -la $REMOTE_PATH/"

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Install dependencies: pip3 install -r requirements.txt" -ForegroundColor Cyan
Write-Host "2. Run bot: python3 backend/bot_modular.py" -ForegroundColor Cyan
