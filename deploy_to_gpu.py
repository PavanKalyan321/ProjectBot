import paramiko
import time
import os

def deploy_aviator_bot():
    """Deploy Aviator bot to GPU server"""
    
    # Server details
    hostname = "142.93.158.30"
    username = "root"
    password = "aviator123"
    
    print(f"Connecting to GPU server: {hostname}")
    
    # SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname, username=username, password=password)
        print("Connected successfully!")
        
        # Commands to deploy bot
        commands = [
            # Clone bot repository
            "cd /root && git clone https://github.com/your-repo/aviator-bot.git || echo 'Repo exists'",
            
            # Install additional dependencies
            "pip3 install paramiko scp",
            
            # Create bot directory structure
            "mkdir -p /root/aviator-bot/backend",
            "mkdir -p /root/aviator-bot/backend/core",
            "mkdir -p /root/aviator-bot/backend/data",
            
            # Set VNC password
            "echo 'aviator123' | vncpasswd -f > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            
            # Start VNC server
            "vncserver :1 -geometry 1920x1080 -depth 24",
            
            # Start web VNC
            "nohup websockify --web=/usr/share/novnc/ 6080 localhost:5901 > /dev/null 2>&1 &",
            
            # Create startup script
            """cat > /root/start_aviator.sh << 'EOF'
#!/bin/bash
export DISPLAY=:1
cd /root/aviator-bot
python3 backend/bot_modular.py
EOF""",
            
            "chmod +x /root/start_aviator.sh",
            
            # Create systemd service
            """cat > /etc/systemd/system/aviator-bot.service << 'EOF'
[Unit]
Description=Aviator Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/aviator-bot
Environment=DISPLAY=:1
ExecStart=/usr/bin/python3 backend/bot_modular.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF""",
            
            "systemctl daemon-reload",
            "systemctl enable aviator-bot"
        ]
        
        # Execute commands
        for cmd in commands:
            print(f"Executing: {cmd[:50]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error and "warning" not in error.lower():
                print(f"Error: {error}")
            if output:
                print(f"Output: {output[:100]}...")
        
        print("\n=== DEPLOYMENT COMPLETE ===")
        print(f"GPU Server: {hostname}")
        print(f"VNC Access: {hostname}:5901")
        print(f"Web VNC: http://{hostname}:6080/vnc.html")
        print(f"Dashboard: http://{hostname}:5000")
        print(f"VNC Password: aviator123")
        
    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy_aviator_bot()