import requests
import json
import time
import subprocess
import os

def create_ssh_key():
    """Generate SSH key pair"""
    try:
        # Generate SSH key
        subprocess.run(['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', 'aviator_key', '-N', ''], 
                      check=True, capture_output=True)
        
        # Read public key
        with open('aviator_key.pub', 'r') as f:
            public_key = f.read().strip()
        
        print("SSH key generated successfully")
        return public_key
    except:
        print("SSH key generation failed - using password authentication")
        return None

def upload_ssh_key(api_token, public_key):
    """Upload SSH key to DigitalOcean"""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": "aviator-bot-key",
        "public_key": public_key
    }
    
    response = requests.post(
        "https://api.digitalocean.com/v2/account/keys",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 201:
        key_data = response.json()['ssh_key']
        print(f"SSH key uploaded - ID: {key_data['id']}")
        return key_data['id']
    else:
        print(f"Failed to upload SSH key: {response.status_code}")
        return None

def create_gpu_droplet(api_token, ssh_key_id=None):
    """Create GPU droplet"""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    ssh_keys = [ssh_key_id] if ssh_key_id else []
    
    payload = {
        "name": "ml-ai-ubuntu-gpu-4000adax1-20gb-tor1",
        "region": "tor1",
        "size": "gpu-4000adax1-20gb", 
        "image": "gpu-h100x1-base",
        "ssh_keys": ssh_keys,
        "backups": False,
        "ipv6": False,
        "monitoring": True,
        "tags": ["aviator-bot"],
        "user_data": """#!/bin/bash
# Aviator Bot Setup
apt update && apt upgrade -y
apt install -y curl wget git python3 python3-pip build-essential
apt install -y xfce4 xfce4-goodies tightvncserver novnc websockify

# Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update && apt install -y google-chrome-stable

# Python packages
apt install -y python3-opencv tesseract-ocr libtesseract-dev
pip3 install flask flask-socketio pandas numpy opencv-python pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook scikit-learn xgboost lightgbm catboost

# Firewall
ufw allow 22 && ufw allow 5901 && ufw allow 5000 && ufw allow 6080
ufw --force enable

# VNC
mkdir -p /root/.vnc
echo '#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &' > /root/.vnc/xstartup
chmod +x /root/.vnc/xstartup

# Enable password authentication for VNC
echo 'root:aviator123' | chpasswd
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh

echo "Aviator Bot GPU server ready!" > /root/setup_complete.txt
""",
        "vpc_uuid": ""
    }
    
    print("Creating GPU droplet...")
    print(f"Name: {payload['name']}")
    print(f"Region: {payload['region']} (Toronto)")
    print(f"Size: {payload['size']}")
    print(f"SSH Keys: {len(ssh_keys)} key(s)")
    
    response = requests.post(
        "https://api.digitalocean.com/v2/droplets",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 202:
        droplet_data = response.json()
        droplet_id = droplet_data['droplet']['id']
        print(f"SUCCESS! Droplet ID: {droplet_id}")
        
        # Wait for active
        print("Waiting for droplet...")
        while True:
            check_response = requests.get(
                f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
                headers=headers
            )
            
            if check_response.status_code == 200:
                droplet = check_response.json()['droplet']
                status = droplet['status']
                
                if status == 'active':
                    ip = droplet['networks']['v4'][0]['ip_address']
                    print(f"\n=== GPU DROPLET READY ===")
                    print(f"IP: {ip}")
                    print(f"Cost: ~$1200+/month")
                    print(f"\nAccess:")
                    print(f"SSH: ssh root@{ip}")
                    if os.path.exists('aviator_key'):
                        print(f"SSH with key: ssh -i aviator_key root@{ip}")
                    print(f"Password: aviator123")
                    print(f"VNC: {ip}:5901")
                    print(f"Web VNC: http://{ip}:6080/vnc.html")
                    print(f"Dashboard: http://{ip}:5000")
                    break
                else:
                    print(f"Status: {status}")
                    time.sleep(15)
            else:
                print(f"Error: {check_response.status_code}")
                break
    else:
        print(f"FAILED: {response.status_code}")
        print(f"Error: {response.text}")

def main():
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    
    # Try to create SSH key
    public_key = create_ssh_key()
    ssh_key_id = None
    
    if public_key:
        ssh_key_id = upload_ssh_key(api_token, public_key)
    
    # Create droplet
    create_gpu_droplet(api_token, ssh_key_id)

if __name__ == "__main__":
    main()