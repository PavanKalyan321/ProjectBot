import paramiko
import os

def deploy_with_ssh_key():
    """Deploy using SSH key"""
    
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"  # Private key file
    
    print(f"Connecting to {hostname} with SSH key...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Load private key
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key)
        print("Connected with SSH key!")
        
        # Setup commands
        setup_commands = [
            # Update system
            "apt update",
            
            # Create bot directory
            "mkdir -p /root/aviator-bot/backend/core",
            "mkdir -p /root/aviator-bot/backend/data",
            
            # Install additional Python packages
            "pip3 install paramiko scp flask-socketio",
            
            # Setup VNC with password
            "mkdir -p /root/.vnc",
            "echo 'aviator123' | vncpasswd -f > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            
            # Kill any existing VNC sessions
            "vncserver -kill :1 || true",
            
            # Start VNC server
            "vncserver :1 -geometry 1920x1080 -depth 24",
            
            # Start web VNC in background
            "pkill -f websockify || true",
            "nohup websockify --web=/usr/share/novnc/ 6080 localhost:5901 > /tmp/novnc.log 2>&1 &",
            
            # Create simple bot starter
            """cat > /root/aviator-bot/start_bot.py << 'EOF'
#!/usr/bin/env python3
print("Aviator Bot GPU Server Ready!")
print("Server IP: 142.93.158.30")
print("VNC Access: 142.93.158.30:5901")
print("Web VNC: http://142.93.158.30:6080/vnc.html")
print("VNC Password: aviator123")
print("")
print("To run the full bot:")
print("1. Connect via VNC")
print("2. Open Chrome browser")
print("3. Navigate to Aviator game")
print("4. Run your bot files")
EOF""",
            
            "chmod +x /root/aviator-bot/start_bot.py",
            
            # Test VNC status
            "ps aux | grep vnc",
            "netstat -tlnp | grep :5901 || echo 'VNC not listening'",
            "netstat -tlnp | grep :6080 || echo 'Web VNC not listening'"
        ]
        
        print("Setting up server...")
        for cmd in setup_commands:
            print(f"Running: {cmd[:50]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if exit_status != 0 and "kill" not in cmd:
                print(f"Command failed: {cmd}")
                if error:
                    print(f"Error: {error}")
            
            if "vnc" in cmd.lower() or "netstat" in cmd:
                print(f"Output: {output}")
        
        print("\n" + "="*50)
        print("🎉 GPU SERVER READY FOR AVIATOR BOT!")
        print("="*50)
        print(f"🌐 Server IP: {hostname}")
        print(f"🖥️  VNC Access: {hostname}:5901")
        print(f"🌐 Web VNC: http://{hostname}:6080/vnc.html")
        print(f"🔑 VNC Password: aviator123")
        print(f"💰 Monthly Cost: ~$1200+")
        print("")
        print("🎯 Next Steps:")
        print("1. Open VNC client or web browser")
        print("2. Connect to the server")
        print("3. Open Chrome browser")
        print("4. Navigate to Aviator game")
        print("5. Upload and run your bot files")
        print("")
        print("🚀 Your GPU server is ready for trading!")
        
    except Exception as e:
        print(f"Deployment failed: {e}")
        print("Make sure the SSH key file 'aviator_key' exists")
    finally:
        ssh.close()

if __name__ == "__main__":
    deploy_with_ssh_key()