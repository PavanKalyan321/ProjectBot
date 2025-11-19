import paramiko
import requests

def diagnose_server():
    hostname = "142.93.158.30"
    username = "root"
    key_file = "aviator_key"
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    droplet_id = "530421083"
    
    # Check droplet status via API
    print("Checking droplet status...")
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(f"https://api.digitalocean.com/v2/droplets/{droplet_id}", headers=headers)
    
    if response.status_code == 200:
        droplet = response.json()['droplet']
        print(f"Status: {droplet['status']}")
        print(f"IP: {droplet['networks']['v4'][0]['ip_address']}")
    
    # Try SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        private_key = paramiko.RSAKey.from_private_key_file(key_file)
        ssh.connect(hostname, username=username, pkey=private_key, timeout=10)
        print("✅ SSH connection successful!")
        
        # Check services
        commands = [
            "systemctl status ssh",
            "netstat -tlnp | grep :22",
            "netstat -tlnp | grep :5901", 
            "netstat -tlnp | grep :6080",
            "ps aux | grep vnc",
            "ufw status"
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            print(f"\n{cmd}:")
            print(output[:200])
        
    except Exception as e:
        print(f"❌ SSH failed: {e}")
        
        # Try to restart the droplet
        print("Attempting to restart droplet...")
        restart_response = requests.post(
            f"https://api.digitalocean.com/v2/droplets/{droplet_id}/actions",
            headers=headers,
            json={"type": "reboot"}
        )
        
        if restart_response.status_code == 201:
            print("✅ Droplet restart initiated")
            print("Wait 2-3 minutes and try again")
        else:
            print("❌ Failed to restart droplet")
    
    finally:
        ssh.close()

if __name__ == "__main__":
    diagnose_server()