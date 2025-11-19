import paramiko
import time

def setup_gpu_server():
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"
    
    print(f"Setting up GPU server: {hostname}")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key)
        print("Connected!")
        
        # Wait for cloud-init to complete
        print("Waiting for initial setup to complete...")
        stdin, stdout, stderr = ssh.exec_command("cloud-init status --wait")
        stdout.read()
        
        # Check if setup completed
        stdin, stdout, stderr = ssh.exec_command("ls -la /root/setup_complete.txt")
        if stdout.read():
            print("Initial setup completed!")
        
        # Install missing packages
        commands = [
            "apt update",
            "apt install -y python3-pip",
            "pip3 install --upgrade pip",
            "apt install -y tigervnc-standalone-server tigervnc-common",
            
            # Setup VNC password
            "mkdir -p /root/.vnc",
            "echo 'aviator123' > /tmp/vncpass.txt",
            "vncpasswd -f < /tmp/vncpass.txt > /root/.vnc/passwd",
            "chmod 600 /root/.vnc/passwd",
            
            # Start VNC
            "export DISPLAY=:1",
            "vncserver :1 -geometry 1920x1080 -depth 24 -localhost no",
            
            # Start web VNC
            "pkill -f websockify || true",
            "nohup websockify --web=/usr/share/novnc/ 6080 localhost:5901 &",
            
            # Check services
            "sleep 5",
            "netstat -tlnp | grep :5901",
            "netstat -tlnp | grep :6080"
        ]
        
        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=60)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if output:
                print(f"Output: {output}")
            if error and exit_status != 0:
                print(f"Error: {error}")
        
        print("\n" + "="*40)
        print("GPU SERVER SETUP COMPLETE!")
        print("="*40)
        print(f"IP: {hostname}")
        print(f"VNC: {hostname}:5901")
        print(f"Web VNC: http://{hostname}:6080/vnc.html")
        print(f"Password: aviator123")
        print("\nYour server is ready!")
        
    except Exception as e:
        print(f"Setup failed: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    setup_gpu_server()