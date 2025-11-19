import requests

def check_ssh_keys(api_token):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(
        "https://api.digitalocean.com/v2/account/keys",
        headers=headers
    )
    
    if response.status_code == 200:
        keys = response.json()['ssh_keys']
        print(f"Found {len(keys)} SSH keys:")
        for key in keys:
            print(f"  ID: {key['id']} - Name: {key['name']}")
        return keys
    else:
        print(f"Error getting SSH keys: {response.status_code}")
        print(response.text)
        return []

if __name__ == "__main__":
    api_token = "dop_v1_4aa58b1f8816a124494c1e20ffa46d2059b9da027fa6275c1a068d6ff4b7c470"
    check_ssh_keys(api_token)