import os
import re
from collections import defaultdict

output_file = "../bitcoin-data/seen_addresses.txt"

subnets = defaultdict(int)

with open(output_file, "r") as file:
    for line in file:
        line = line.strip()
        match_ipv4 = re.match(r"(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}", line)
        match_ipv6 = re.match(r"(([0-9a-fA-F]{0,4}:){1,7}[0-9a-fA-F]{0,4})[:/]", line)
        if match_ipv4:
            subnet = match_ipv4.group(1)
            subnet_parts = subnet.split(".")
            subnet_num = ".".join(subnet_parts)
            subnets[subnet_num] += 1
        elif match_ipv6:
            subnet = match_ipv6.group(1)
            subnets[subnet] += 1

print(f"Subnetmask: 255.255.255.0 - /24")
for subnet_num, count in sorted(subnets.items()):
    if count > 1:  # Exclude subnets with only one peer
        print(f"Subnet: {subnet_num}, Peers: {count}")
