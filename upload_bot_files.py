import paramiko
import os
from scp import SCPClient

def upload_aviator_bot():
    """Upload all bot files to GPU server"""
    
    hostname = "142.93.158.30"
    username = "root" 
    password = "aviator123"
    
    print(f"Uploading Aviator bot to {hostname}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(hostname, username=username, password=password)
        print("Connected!")
        
        # Create directories
        ssh.exec_command("mkdir -p /root/aviator-bot/backend/core")
        ssh.exec_command("mkdir -p /root/aviator-bot/backend/data")
        ssh.exec_command("mkdir -p /root/aviator-bot/backend/dashboard/templates")
        
        # Upload files using SCP
        with SCPClient(ssh.get_transport()) as scp:
            
            # Core bot files
            files_to_upload = [
                ("backend/bot_modular.py", "/root/aviator-bot/backend/"),
                ("backend/core/ml_signal_generator.py", "/root/aviator-bot/backend/core/"),
                ("backend/cloud_sync.py", "/root/aviator-bot/backend/"),
                ("backend/pattern_predictor.py", "/root/aviator-bot/backend/"),
                ("backend/mobile_notifier.py", "/root/aviator-bot/backend/"),
                ("backend/seasonal_analyzer.py", "/root/aviator-bot/backend/"),
                ("requirements.txt", "/root/aviator-bot/"),
                ("run_dashboard.py", "/root/aviator-bot/")
            ]
            
            for local_file, remote_path in files_to_upload:
                if os.path.exists(local_file):
                    print(f"Uploading {local_file}...")
                    scp.put(local_file, remote_path)
                else:
                    print(f"File not found: {local_file}")
        
        # Install requirements
        print("Installing Python requirements...")
        ssh.exec_command("cd /root/aviator-bot && pip3 install -r requirements.txt")
        
        # Setup VNC
        print("Setting up VNC...")
        commands = [
            "echo 'aviator123' | vncpasswd -f > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            "vncserver :1 -geometry 1920x1080 -depth 24",
            "nohup websockify --web=/usr/share/novnc/ 6080 localhost:5901 > /dev/null 2>&1 &"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            time.sleep(2)
        
        print("\n=== UPLOAD COMPLETE ===")
        print(f"Server: {hostname}")
        print(f"VNC: {hostname}:5901 (password: aviator123)")
        print(f"Web VNC: http://{hostname}:6080/vnc.html")
        print(f"SSH: ssh root@{hostname}")
        
        print("\nNext steps:")
        print("1. Connect via VNC")
        print("2. Open Chrome browser")
        print("3. Navigate to Aviator game")
        print("4. Run: cd /root/aviator-bot && python3 backend/bot_modular.py")
        
    except Exception as e:
        print(f"Upload failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    upload_aviator_bot()