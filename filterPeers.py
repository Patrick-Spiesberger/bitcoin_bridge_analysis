import os
import json
import shutil
import re

source_dir = '/media/volume/bitcoin-data/daily_json_files'
ipv4_dir = '/media/volume/bitcoin-data/daily_ipv4'
ipv6_dir = '/media/volume/bitcoin-data/daily_ipv6'
onion_dir = '/media/volume/bitcoin-data/daily_onion'

files = os.listdir(source_dir)

for filename in files:
    source_file = os.path.join(source_dir, filename)

    with open(source_file, 'r') as file:
        data = json.load(file)

    ipv4_peers = []
    ipv6_peers = []
    onion_peers = []

    for peer in data:
        addr = peer.get('addr', '')

        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', addr):
            ipv4_peers.append(peer)
        elif '.onion' in addr:
            onion_peers.append(peer)
        elif re.match(r'[a-fA-F0-9:]+', addr):
            ipv6_peers.append(peer)

    ipv4_dest_file = os.path.join(ipv4_dir, filename)
    ipv6_dest_file = os.path.join(ipv6_dir, filename)
    onion_dest_file = os.path.join(onion_dir, filename)

    with open(ipv4_dest_file, 'w') as file:
        json.dump(ipv4_peers, file, indent=4)

    with open(ipv6_dest_file, 'w') as file:
        json.dump(ipv6_peers, file, indent=4)

    with open(onion_dest_file, 'w') as file:
        json.dump(onion_peers, file, indent=4)
