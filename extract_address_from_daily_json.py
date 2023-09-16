import os
import json
import re

data_directory = "../bitcoin-data/daily_json_files/"
output_file = "../bitcoin-data/seen_addresses.txt"

if os.path.exists(output_file):
    os.remove(output_file)

onion_addresses = set()
ipv4_addresses = set()
ipv6_addresses = set()

onion_regex = r"^(.*\.onion)(:\d+)?$"

for filename in os.listdir(data_directory):
    if filename.endswith(".json"):
        file_path = os.path.join(data_directory, filename)
        with open(file_path, "r") as file:
            try:
                json_data = json.load(file)
                for entry in json_data:
                    if "addr" in entry:
                        address = entry["addr"]
                        match = re.match(onion_regex, address)
                        if match:
                            onion_address = match.group(1)
                            port = match.group(2)
                            onion_addresses.add(address)
                        elif "." in address:
                            ipv4_addresses.add(address)
                        else:
                            ipv6_addresses.add(address)
            except json.JSONDecodeError:
                print(f"Error decoding JSON in file: {file_path}")

onion_addresses = sorted(onion_addresses)
ipv4_addresses = sorted(ipv4_addresses)
ipv6_addresses = sorted(ipv6_addresses)

with open(output_file, "w") as output:
    for address in onion_addresses:
        output.write(address + "\n")

    for address in ipv4_addresses:
        output.write(address + "\n")

    for address in ipv6_addresses:
        output.write(address + "\n")

print("Address extraction complete.")
