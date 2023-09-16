import os
import subprocess
import json
import re
from datetime import datetime, timedelta

DUAL_IPV4 = 0
DUAL_IPV4_ONION = 0
DUAL_ONION_ONION = 0
FILE_COUNTS_TWO = 0
STATIC_ANALYSIS = 0
CONNECT_ANALYSIS = 0
HEART_ANALYSIS = 0
HASH_ANALYSIS = 0
processed_addresses = set()
processed_addr = set()
peer_count = 0


def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Error executing command: {result.stderr}")
        return None

def parse_results(output):
    parsed_results = []
    lines = output.strip().split('\n')
    for line in lines:
        parts = line.split()
        if len(parts) >= 3:
            count = int(parts[0])
            addresses = f"{parts[1]} {parts[2]}"
            parsed_results.append((count, addresses))
    return parsed_results

def parse_ping_detail(detail_content, addresses):
    blocks = detail_content.split('\n\n')
    parsed_info = {}
    addr = addresses.split("; ")
    for block in blocks:
        if addr[0] in block and addr[1] in block:
            parsed_info['Detail'] = block
    return parsed_info

def parse_static_detail(detail_content, addresses):
    lines = detail_content.split('\n')
    parsed_info = {}
    common_changes = {}
    current_key = None
    found_addresses = False
    for line in lines:
        if addresses in line:
            found_addresses = True
            parsed_info['Address'] = addresses
        elif found_addresses and line.startswith("Common Changes:"):
            current_key = "Common Changes"
        elif found_addresses and current_key == "Common Changes" and line.startswith("    "):
            key, value = line.strip().split(': ', 1)
            common_changes[key] = value
        elif line.startswith("date:"):
            parsed_info['Date'] = line.split(': ')[1]
        elif found_addresses and line.startswith("-----"):
            parsed_info[current_key] = common_changes
            break

    return parsed_info

def parse_connect_detail(detail_content, addresses):
    lines = detail_content.split('\n')
    parsed_info = {}
    addr = addresses.split('; ')
    for line in lines:
        if addr[0] in line and addr[1] in line:
            parsed_info['Address'] = addresses
            parsed_info['Event'] = line
    return parsed_info

def process_log_file(file_path):
    command = f"sort {file_path} | uniq -c"
    output = run_command(command)
    
    if output:
        parsed_results = parse_results(output)
        return parsed_results
    return []

def process_ping_folder(folder_path, addresses):
    ping_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    detail_info = {}
    addr = addresses.split("; ")
    for ping_file in ping_files:
        file_path = os.path.join(folder_path, ping_file)
        with open(file_path, 'r') as f:
            file_content = f.read()
            if addr[0] in file_content and addr[1] in file_content:
                parsed_info = parse_ping_detail(file_content, addresses)
                if parsed_info:
                    detail_info[ping_file] = parsed_info

    return detail_info

def process_detail_file(detail_path, addresses):
    detail_info = {}

    with open(detail_path, 'r') as f:
        file_content = f.read()
        if "ping" in detail_path:
            parsed_info = parse_ping_detail(file_content, addresses)
        elif "static" in detail_path:
            parsed_info = parse_static_detail(file_content, addresses)
        elif "connect" in detail_path:
            parsed_info = parse_connect_detail(file_content, addresses)
        elif "disconnect" in detail_path:
            parsed_info = parse_connect_detail(file_content, addresses)
        detail_info[detail_path] = parsed_info

    return detail_info

def format_output(parsed_info):
    formatted = ""
    for key, value in parsed_info.items():
        if isinstance(value, dict):
            formatted += f"{key}:\n"
            for sub_key, sub_value in value.items():
                formatted += f"    {sub_key}: {sub_value}\n"
        else:
            formatted += f"{key}: {value}\n"
    return formatted

def print_peer_info(addresses, peerinfo):
    addr_list = addresses.split("; ")
    found_peers = []

    for peer in peerinfo:
        for addr in addr_list:
            if "addr" in peer and peer["addr"].startswith(addr):
                found_peers.append(peer)
                addr_list.remove(addr)

    if found_peers:
        print(f"Currently Connected:")
        for peer in found_peers:
            print(peer)
            print(f"\n")

    data_folder = "../bitcoin-data/daily_json_files/"
    
    for addr in addr_list:
        matching_files = []
        for filename in os.listdir(data_folder):
            try:
                if filename.endswith(".json"):
                    file_path = os.path.join(data_folder, filename)
                    with open(file_path, "r") as file:
                        data = json.load(file)
                        if any(peer.get("addr", "").startswith(addr) for peer in data):
                            matching_files.append(file_path)
            except ValueError:
                continue

        try:
            if matching_files:
                newest_file = max(matching_files, key=os.path.getctime)
                with open(newest_file, "r") as file:
                    data = json.load(file)
                for peer in data:
                    if peer.get("addr", "").startswith(addr):
                        print(f"Last Seen in {newest_file}")
                        print(peer)
                        print(f"\n")
        except ValueError:
            print(f"Newest File {filename} is broken")
            continue

def address_combination_type(addresses):
    global DUAL_IPV4
    global DUAL_IPV4_ONION
    global DUAL_ONION_ONION
    global processed_addresses, processed_addr
    global peer_count

    addr1, addr2 = addresses.split("; ")

    ipv4_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?$')
    onion_pattern = re.compile(r'^[a-z2-7]{16,56}\.onion(:\d+)?$')

    if re.match(ipv4_pattern, addr1) and re.match(ipv4_pattern, addr2):
        DUAL_IPV4 += 1
    elif re.match(ipv4_pattern, addr1) and re.match(onion_pattern, addr2):
        DUAL_IPV4_ONION += 1
    elif re.match(onion_pattern, addr1) and re.match(ipv4_pattern, addr2):
        DUAL_IPV4_ONION += 1
    elif re.match(onion_pattern, addr1) and re.match(onion_pattern, addr2):
        DUAL_ONION_ONION += 1

    processed_addresses.add(addresses)

    if (not(addr1 in processed_addr) or not(addr2 in processed_addr)):
        peer_count += 1

    processed_addr.add(addr1)
    processed_addr.add(addr2)

def main():
    global DUAL_IPV4, DUAL_IPV4_ONION, DUAL_ONION_ONION, FILE_COUNTS_TWO, STATIC_ANALYSIS, CONNECT_ANALYSIS, HEART_ANALYSIS, HASH_ANALYSIS, peer_count
    folder_path = "../bitcoin-data/analysis/suspect_addr"
    detail_folder = "../bitcoin-data/analysis/detail"
    ping_folder = "../bitcoin-data/analysis/detail/ping"
    log_files = [
        "connect_sus.log",
        "disconnect_sus.log",
        "hashes_sus.log",
        "ping_sus.log",
        "static_sus.log"
    ]

    address_counts = {}
    unique_address_pairs = set()  # Set to store unique address pairs
    added_address_pairs = 0  # Counter for added address pairs

    peer_info_cmd = run_command("bitcoin-cli getpeerinfo")
    peerinfo = json.dumps(peer_info_cmd)

    for log_file in log_files:
        file_path = os.path.join(folder_path, log_file)
        parsed_results = process_log_file(file_path)

        for count, addresses in parsed_results:
            if addresses not in address_counts:
                address_counts[addresses] = {}
            address_counts[addresses][log_file] = count

    for addresses, file_counts in address_counts.items():
        unique_address_pairs.add(addresses)
        if len(file_counts) >= 1:
            if len(file_counts) >= 2:
                FILE_COUNTS_TWO += 1

            for log_file, count in file_counts.items():
                if (not(log_file == "static_sus.log") and (count < 3)):
                     continue


                if (log_file == "ping_sus.log" and (count < 50)):
                     continue

                if (count < 2):
                    continue

                #if (log_file == "hashes_sus.log"):
                #     continue


                if(addresses in processed_addresses):
                    continue

                print("=" * 80)
                print("Addresses:", addresses, "\n")

                print(f"In {log_file}: {count} occurrences")

                address_combination_type(addresses)

                if log_file == "ping_sus.log":
                    HEART_ANALYSIS += 1
                    detail_info = process_ping_folder(ping_folder, addresses)
                    if detail_info:
                        for file_name, parsed_info in detail_info.items():
                            print(f"File: {file_name}")
                            formatted_content = format_output(parsed_info)
                            print(formatted_content)
                
                elif (log_file == "connect_sus.log" or log_file == "disconnect_sus.log"):
                    CONNECT_ANALYSIS = +1
                    detail_file = os.path.join(detail_folder, log_file.replace("_sus.log", "_count.log"))
                    if os.path.isfile(detail_file):
                        detail_info = process_detail_file(detail_file, addresses)
                        if detail_info:
                            for file_name, parsed_info in detail_info.items():
                                print(f"File: {file_name}")
                                formatted_content = format_output(parsed_info)
                                print(formatted_content)
                    addr_list = addresses.split("; ")
                    cmd1 = f"grep {addr_list[0]} ../peer_connect.log | wc -l"
                    cmd2 = f"grep {addr_list[1]} ../peer_connect.log | wc -l"
                    if (log_file == "disconnect_sus.log"):
                        cmd1 = f"grep {addr_list[0]} ../peer_disconnect_addr.log | wc -l"
                        cmd2 = f"grep {addr_list[1]} ../peer_disconnect_addr.log | wc -l"

                    print(f"Non suspicious behavior of {addr_list[0]}: {int(run_command(cmd1)) - count}")
                    print(f"Non suspicious behavior of {addr_list[1]}: {int(run_command(cmd2)) - count}\n")

                elif log_file.endswith("hashes_sus.log"):
                    HASH_ANALYSIS += 1
                    detail_file = os.path.join(detail_folder, log_file.replace("_sus.log", "_analysis_output.log"))
                    if os.path.isfile(detail_file):
                        detail_info = process_detail_file(detail_file, addresses)
                        if detail_info:
                            for file_name, parsed_info in detail_info.items():
                                print(f"File: {file_name}")
                                formatted_content = format_output(parsed_info)
                                print(formatted_content)

                elif log_file.endswith("static_sus.log"):
                    STATIC_ANALYSIS += 1
                    detail_file = os.path.join(detail_folder, log_file.replace("_sus.log", "_analysis_output.log"))
                    if os.path.isfile(detail_file):
                        detail_info = process_detail_file(detail_file, addresses)
                        if detail_info:
                            for file_name, parsed_info in detail_info.items():
                                print(f"File: {file_name}")
                                formatted_content = format_output(parsed_info)
                                print(formatted_content)

                print_peer_info(addresses, peerinfo)

    print("=" * 80)


    print(f"Count of Adresses: {len(unique_address_pairs)}")
    print(f"More than one entry: {FILE_COUNTS_TWO}")
    print(f"Static Analysis: {STATIC_ANALYSIS}")
    print(f"Connect Analysis: {CONNECT_ANALYSIS}")
    print(f"Ping Analysis: {HEART_ANALYSIS}")
    print(f"Hash Analysis: {HASH_ANALYSIS}")
    print(f"Dual-Stacked IP-Addresses: {DUAL_IPV4}")
    print(f"Dual-Stacked IP-ONION-Addresses: {DUAL_IPV4_ONION}")
    print(f"Dual-Stacked ONION-ONION-Addresses: {DUAL_ONION_ONION}")
    print(f"Unique Peers: {peer_count}")


if __name__ == "__main__":
    main()
