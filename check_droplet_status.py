import requests
import time

def check_droplet_status():
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    droplet_id = "530421083"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        droplet = response.json()['droplet']
        status = droplet['status']
        ip = droplet['networks']['v4'][0]['ip_address']
        
        print(f"Droplet Status: {status}")
        print(f"IP Address: {ip}")
        
        if status == 'active':
            print("Server is ready! Try connecting now:")
            print(f"ssh -i aviator_key root@{ip}")
        else:
            print("Server is still starting up. Wait a moment...")
    else:
        print(f"Error checking status: {response.status_code}")

if __name__ == "__main__":
    check_droplet_status()