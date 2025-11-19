import paramiko

def fix_vnc_server():
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key)
        print("Connected to server!")
        
        # Fix VNC setup
        commands = [
            # Kill any existing VNC sessions
            "vncserver -kill :1 || true",
            "vncserver -kill :2 || true",
            
            # Install proper VNC server
            "apt update",
            "apt install -y tigervnc-standalone-server tigervnc-common",
            
            # Create VNC password file
            "mkdir -p /root/.vnc",
            "echo 'aviator123' | vncpasswd -f > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            
            # Create proper xstartup
            """cat > /root/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec startxfce4
EOF""",
            
            "chmod +x /root/.vnc/xstartup",
            
            # Start VNC server with no localhost restriction
            "vncserver :1 -geometry 1920x1080 -depth 24 -localhost no",
            
            # Check if VNC is running
            "netstat -tlnp | grep :5901",
            "ps aux | grep vnc"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd[:50]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "netstat" in cmd or "ps aux" in cmd:
                print(f"Output: {output}")
            
            if exit_status != 0 and "kill" not in cmd:
                print(f"Warning: {cmd} failed")
                if error:
                    print(f"Error: {error}")
        
        print("\n" + "="*50)
        print("VNC SERVER FIXED!")
        print("="*50)
        print(f"Server: {hostname}:5901")
        print("Password: aviator123")
        print("\nTry connecting with RealVNC now!")
        
    except Exception as e:
        print(f"Failed to fix VNC: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    fix_vnc_server()