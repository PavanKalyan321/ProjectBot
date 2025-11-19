import requests
import time

def restart_droplet():
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    droplet_id = "530421083"
    
    headers = {"Authorization": f"Bearer {api_token}"}
    
    print("Restarting droplet...")
    restart_response = requests.post(
        f"https://api.digitalocean.com/v2/droplets/{droplet_id}/actions",
        headers=headers,
        json={"type": "reboot"}
    )
    
    if restart_response.status_code == 201:
        print("Droplet restart initiated")
        print("Waiting for restart to complete...")
        
        # Wait for restart
        for i in range(30):
            time.sleep(10)
            
            # Check status
            response = requests.get(f"https://api.digitalocean.com/v2/droplets/{droplet_id}", headers=headers)
            if response.status_code == 200:
                droplet = response.json()['droplet']
                status = droplet['status']
                print(f"Status: {status}")
                
                if status == 'active':
                    ip = droplet['networks']['v4'][0]['ip_address']
                    print(f"Server is back online: {ip}")
                    print("\nNow try:")
                    print(f"ssh -i aviator_key root@{ip}")
                    print(f"Web VNC: http://{ip}:6080/vnc.html")
                    break
        else:
            print("Restart taking longer than expected")
    else:
        print(f"Failed to restart: {restart_response.status_code}")

if __name__ == "__main__":
    restart_droplet()