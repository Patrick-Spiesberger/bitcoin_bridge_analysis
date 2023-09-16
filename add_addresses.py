import subprocess
import json

def add_peers(addresses):
    for address in addresses:
        result = subprocess.run(['bitcoin-cli', 'addnode', address, 'onetry'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Added peer: {address}")
        else:
            print(f"Failed to add peer: {address}")
            print(result.stderr)

# Run 'bitcoin-cli getnodeaddresses 80000' command and parse the JSON response
result = subprocess.run(['bitcoin-cli', 'getnodeaddresses', '80000'], capture_output=True, text=True)
if result.returncode == 0:
    response = result.stdout.strip()
    data = json.loads(response)
    addresses = [entry['address'] for entry in data]
    add_peers(addresses)
else:
    print("Failed to retrieve node addresses.")
    print(result.stderr)
