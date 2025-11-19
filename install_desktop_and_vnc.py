import paramiko

def install_desktop_and_vnc():
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key)
        print("Connected!")
        
        # Install desktop environment and VNC
        commands = [
            # Install desktop environment
            "apt update",
            "DEBIAN_FRONTEND=noninteractive apt install -y xfce4 xfce4-goodies",
            
            # Install VNC server
            "apt install -y tigervnc-standalone-server",
            
            # Create VNC password
            "mkdir -p /root/.vnc",
            "echo 'aviator123' | vncpasswd -f > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            
            # Create working xstartup
            """cat > /root/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
/usr/bin/startxfce4 &
EOF""",
            
            "chmod +x /root/.vnc/xstartup",
            
            # Start VNC server
            "vncserver :1 -geometry 1920x1080 -depth 24 -localhost no",
            
            # Check status
            "netstat -tlnp | grep :5901"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd[:60]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "netstat" in cmd:
                print(f"VNC Status: {output}")
            
            if exit_status != 0 and "netstat" not in cmd:
                print(f"Command failed: {cmd[:30]}")
                if error:
                    print(f"Error: {error[:200]}")
        
        print("\n" + "="*40)
        print("DESKTOP & VNC INSTALLED!")
        print("="*40)
        print("Connect with RealVNC:")
        print(f"Server: {hostname}:5901")
        print("Password: aviator123")
        
    except Exception as e:
        print(f"Installation failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    install_desktop_and_vnc()