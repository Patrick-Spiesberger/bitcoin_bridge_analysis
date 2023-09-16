import os
import json
from datetime import datetime

folder_path = "../bitcoin-data/daily_json_files"
os.makedirs(folder_path, exist_ok=True)

date_format = "%d-%m-%Y"
filename = os.path.join(folder_path, datetime.now().strftime(date_format) + ".json")

if os.path.exists(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
else:
    data = []

output = os.popen("bitcoin-cli getpeerinfo").read()
peer_info = json.loads(output)

# Check for new peers
new_peers = []
for peer in peer_info:
    if not any(peer["addr"] == p["addr"] for p in data):
        new_peers.append(peer)

# Add new peers to the data list
data.extend(new_peers)

# Save the data to the file with pretty formatting
with open(filename, 'w') as file:
    json.dump(data, file, indent=4)

if new_peers:
    num_new_peers = len(new_peers)
    print(f"{num_new_peers} new peer(s) added.")
else:
    print("No new peers added.")

print("Peer information successfully saved.")
