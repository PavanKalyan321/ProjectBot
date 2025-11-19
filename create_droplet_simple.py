import requests
import json
import time
import sys

def create_droplet(api_token):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
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
        "user_data": """#!/bin/bash
apt update && apt upgrade -y
apt install -y curl wget git python3 python3-pip build-essential
apt install -y xfce4 xfce4-goodies tightvncserver novnc websockify
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt update && apt install -y google-chrome-stable
apt install -y python3-opencv tesseract-ocr libtesseract-dev
pip3 install flask flask-socketio pandas numpy opencv-python pytesseract mss pyautogui keyboard
pip3 install gspread google-auth requests discord-webhook scikit-learn xgboost lightgbm catboost
apt install -y ufw
ufw allow 22 && ufw allow 5901 && ufw allow 5000 && ufw allow 6080
ufw --force enable
mkdir -p /root/.vnc
echo '#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &' > /root/.vnc/xstartup
chmod +x /root/.vnc/xstartup
echo "Setup completed" > /root/setup_complete.txt
""",
        "vpc_uuid": ""
    }
    
    print("Creating GPU droplet...")
    print(f"Name: {payload['name']}")
    print(f"Region: {payload['region']}")
    print(f"Size: {payload['size']}")
    
    response = requests.post(
        "https://api.digitalocean.com/v2/droplets",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 202:
        droplet_data = response.json()
        droplet_id = droplet_data['droplet']['id']
        print(f"SUCCESS! Droplet created with ID: {droplet_id}")
        
        print("Waiting for droplet to become active...")
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
                    print(f"DROPLET IS ACTIVE!")
                    print(f"IP Address: {ip}")
                    print(f"Monthly Cost: ~$1200+")
                    print(f"\nAccess Instructions:")
                    print(f"SSH: ssh root@{ip}")
                    print(f"VNC: {ip}:5901")
                    print(f"Web VNC: http://{ip}:6080/vnc.html")
                    print(f"Dashboard: http://{ip}:5000")
                    break
                else:
                    print(f"Status: {status} - waiting...")
                    time.sleep(15)
            else:
                print(f"Error checking status: {check_response.status_code}")
                break
    else:
        print(f"FAILED to create droplet: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    create_droplet(api_token)