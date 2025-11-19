import paramiko

def simple_vnc_setup():
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key)
        print("Connected!")
        
        commands = [
            # Kill existing VNC
            "vncserver -kill :1 || true",
            
            # Install basic desktop
            "apt install -y ubuntu-desktop-minimal",
            
            # Simple xstartup with gnome
            """cat > /root/.vnc/xstartup << 'EOF'
#!/bin/bash
export XKL_XMODMAP_DISABLE=1
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
gnome-session &
EOF""",
            
            "chmod +x /root/.vnc/xstartup",
            
            # Start VNC
            "vncserver :1 -geometry 1920x1080 -depth 24 -localhost no",
            
            # Check if running
            "netstat -tlnp | grep :5901"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd[:50]}...")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            
            if "netstat" in cmd and output:
                print("✅ VNC Server is running!")
                print(f"Output: {output}")
                break
        
        print("\n🎉 VNC Setup Complete!")
        print(f"Connect to: {hostname}:5901")
        print("Password: aviator123")
        
    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    simple_vnc_setup()