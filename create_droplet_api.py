#!/usr/bin/env python3
"""
DigitalOcean GPU Droplet Creator for Aviator Bot
Usage: python create_droplet_api.py --token YOUR_API_TOKEN
"""

import requests
import json
import time
import argparse
import sys

class DigitalOceanDropletCreator:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.digitalocean.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_gpu_droplet(self, name="ml-ai-ubuntu-gpu-4000adax1-20gb-tor1"):
        """Create GPU droplet with your exact configuration"""
        
        payload = {
            "name": name,
            "region": "tor1",  # Toronto datacenter
            "size": "gpu-4000adax1-20gb",  # RTX 4000 Ada with 20GB
            "image": "gpu-h100x1-base",  # GPU base image
            "ssh_keys": [],  # Add your SSH key IDs here
            "backups": False,
            "ipv6": False,
            "monitoring": True,
            "tags": [],
            "user_data": self._get_user_data_script(),
            "vpc_uuid": ""
        }
        
        print(f"🚀 Creating GPU droplet: {name}")
        print(f"📍 Region: {payload['region']}")
        print(f"💻 Size: {payload['size']}")
        print(f"🖥️  Image: {payload['image']}")
        
        response = requests.post(
            f"{self.base_url}/droplets",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 202:
            droplet_data = response.json()
            droplet_id = droplet_data['droplet']['id']
            print(f"✅ Droplet created successfully!")
            print(f"🆔 Droplet ID: {droplet_id}")
            
            # Wait for droplet to be active
            self._wait_for_droplet_active(droplet_id)
            return droplet_id
        else:
            print(f"❌ Failed to create droplet: {response.status_code}")
            print(f"Error: {response.text}")
            return None
    
    def _get_user_data_script(self):
        """Cloud-init script to setup the droplet automatically"""
        return """#!/bin/bash
# Aviator Bot GPU Server Auto-Setup

# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git python3 python3-pip build-essential

# Install desktop environment
apt install -y xfce4 xfce4-goodies tightvncserver

# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Install Python dependencies
apt install -y python3-opencv tesseract-ocr libtesseract-dev
pip3 install flask flask-socketio pandas numpy opencv-python
pip3 install pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook
pip3 install scikit-learn xgboost lightgbm catboost

# Install noVNC for web access
apt install -y novnc websockify

# Setup firewall
apt install -y ufw
ufw allow 22 && ufw allow 5901 && ufw allow 5000 && ufw allow 6080
ufw --force enable

# Create VNC startup script
mkdir -p /root/.vnc
cat > /root/.vnc/xstartup << 'EOF'
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
chmod +x /root/.vnc/xstartup

# Create setup completion marker
touch /root/setup_complete.txt
echo "Aviator Bot GPU server setup completed at $(date)" > /root/setup_complete.txt
"""
    
    def _wait_for_droplet_active(self, droplet_id):
        """Wait for droplet to become active"""
        print("⏳ Waiting for droplet to become active...")
        
        while True:
            response = requests.get(
                f"{self.base_url}/droplets/{droplet_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                droplet = response.json()['droplet']
                status = droplet['status']
                
                if status == 'active':
                    ip_address = droplet['networks']['v4'][0]['ip_address']
                    print(f"✅ Droplet is active!")
                    print(f"🌐 IP Address: {ip_address}")
                    print(f"💰 Monthly Cost: ~$1200+ (H100 GPU base)")
                    print("\n🎯 Next Steps:")
                    print(f"1. SSH: ssh root@{ip_address}")
                    print(f"2. Set VNC password: vncserver :1")
                    print(f"3. Clone bot: git clone your-repo")
                    print(f"4. VNC access: {ip_address}:5901")
                    print(f"5. Web VNC: http://{ip_address}:6080/vnc.html")
                    break
                else:
                    print(f"Status: {status} - waiting...")
                    time.sleep(10)
            else:
                print(f"Error checking status: {response.status_code}")
                break
    
    def list_ssh_keys(self):
        """List available SSH keys"""
        response = requests.get(f"{self.base_url}/account/keys", headers=self.headers)
        if response.status_code == 200:
            keys = response.json()['ssh_keys']
            print("📋 Available SSH Keys:")
            for key in keys:
                print(f"  ID: {key['id']} - {key['name']}")
            return keys
        return []
    
    def get_regions(self):
        """Get available regions with GPU support"""
        response = requests.get(f"{self.base_url}/regions", headers=self.headers)
        if response.status_code == 200:
            regions = response.json()['regions']
            gpu_regions = [r for r in regions if 'gpu' in r.get('features', [])]
            print("🌍 GPU-enabled regions:")
            for region in gpu_regions:
                print(f"  {region['slug']} - {region['name']}")
            return gpu_regions
        return []

def main():
    parser = argparse.ArgumentParser(description='Create DigitalOcean GPU droplet for Aviator Bot')
    parser.add_argument('--token', required=True, help='DigitalOcean API token')
    parser.add_argument('--name', default='aviator-bot-gpu', help='Droplet name')
    parser.add_argument('--list-keys', action='store_true', help='List SSH keys')
    parser.add_argument('--list-regions', action='store_true', help='List GPU regions')
    
    args = parser.parse_args()
    
    creator = DigitalOceanDropletCreator(args.token)
    
    if args.list_keys:
        creator.list_ssh_keys()
        return
    
    if args.list_regions:
        creator.get_regions()
        return
    
    # Create the droplet
    droplet_id = creator.create_gpu_droplet(args.name)
    
    if droplet_id:
        print(f"\n🎉 Success! Your Aviator Bot GPU server is ready!")
        print(f"💡 Remember to add your SSH key ID to the payload for secure access")

if __name__ == "__main__":
    main()