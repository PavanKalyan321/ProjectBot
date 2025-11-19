#!/usr/bin/env python3
"""
Create DigitalOcean droplet with your exact payload
Usage: python create_with_payload.py YOUR_API_TOKEN
"""

import requests
import json
import time
import sys

def create_droplet_with_payload(api_token):
    """Create droplet using your exact payload"""
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Your exact payload
    payload = {
        "name": "ml-ai-ubuntu-gpu-4000adax1-20gb-tor1",
        "region": "tor1",
        "size": "gpu-4000adax1-20gb", 
        "image": "gpu-h100x1-base",
        "ssh_keys": [],
        "backups": False,
        "ipv6": False,
        "monitoring": True,
        "tags": [],
        "user_data": get_aviator_setup_script(),
        "vpc_uuid": ""
    }
    
    print("🚀 Creating droplet with your payload...")
    print(f"📛 Name: {payload['name']}")
    print(f"📍 Region: {payload['region']} (Toronto)")
    print(f"💻 Size: {payload['size']}")
    print(f"🖥️  Image: {payload['image']}")
    
    response = requests.post(
        "https://api.digitalocean.com/v2/droplets",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 202:
        droplet_data = response.json()
        droplet_id = droplet_data['droplet']['id']
        print(f"✅ Droplet created!")
        print(f"🆔 ID: {droplet_id}")
        
        # Wait for active status
        wait_for_active(api_token, droplet_id)
        return droplet_id
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Error: {response.text}")
        return None

def get_aviator_setup_script():
    """Setup script for Aviator bot"""
    return """#!/bin/bash
# Aviator Bot Setup on GPU H100 Base

apt update && apt upgrade -y
apt install -y curl wget git python3 python3-pip build-essential
apt install -y xfce4 xfce4-goodies tightvncserver novnc websockify

# Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update && apt install -y google-chrome-stable

# Python deps
apt install -y python3-opencv tesseract-ocr libtesseract-dev
pip3 install flask flask-socketio pandas numpy opencv-python pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook scikit-learn xgboost lightgbm catboost

# Firewall
apt install -y ufw
ufw allow 22 && ufw allow 5901 && ufw allow 5000 && ufw allow 6080
ufw --force enable

# VNC setup
mkdir -p /root/.vnc
echo '#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &' > /root/.vnc/xstartup
chmod +x /root/.vnc/xstartup

echo "Setup completed at $(date)" > /root/setup_complete.txt
"""

def wait_for_active(api_token, droplet_id):
    """Wait for droplet to become active"""
    headers = {"Authorization": f"Bearer {api_token}"}
    
    print("⏳ Waiting for droplet...")
    while True:
        response = requests.get(
            f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            droplet = response.json()['droplet']
            status = droplet['status']
            
            if status == 'active':
                ip = droplet['networks']['v4'][0]['ip_address']
                print(f"✅ Active!")
                print(f"🌐 IP: {ip}")
                print(f"💰 Cost: ~$1200+/month")
                print(f"\n🎯 Access:")
                print(f"SSH: ssh root@{ip}")
                print(f"VNC: {ip}:5901")
                print(f"Web: http://{ip}:6080/vnc.html")
                break
            else:
                print(f"Status: {status}")
                time.sleep(15)
        else:
            print(f"Error: {response.status_code}")
            break

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_with_payload.py YOUR_API_TOKEN")
        print("\nGet token from: https://cloud.digitalocean.com/account/api/tokens")
        sys.exit(1)
    
    api_token = sys.argv[1]
    create_droplet_with_payload(api_token)