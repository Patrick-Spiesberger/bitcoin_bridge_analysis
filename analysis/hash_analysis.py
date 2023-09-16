import os
from datetime import datetime, timedelta
from tqdm import tqdm

def parse_data_file(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
        lines = data.strip().split("\n")
        parsed_data = []
        current_peer = None
        current_time = None
        current_transactions = []

        for line in lines:
            if line.startswith("Peer:"):
                if current_peer is not None:
                    parsed_data.append({"Peer": current_peer, "Time": current_time, "Transaktionen": current_transactions})
                    current_transactions = []

                try:
                    current_peer = line.split("Peer: ")[1].split(",")[0]
                    current_time = line.split("Time: ")[1].split(",")[0]
                    inventory_hash = line.split(", Inventory Hash: ")[1][10:]
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    return []
                while inventory_hash:
                    transaction = inventory_hash[:64]
                    current_transactions.append(transaction)
                    if len(inventory_hash) > 64:
                        inventory_hash = inventory_hash[72:]  # Skip 8 characters for the next transaction
                    else:
                        break

        if current_peer is not None:
            parsed_data.append({"Peer": current_peer, "Time": current_time, "Transaktionen": current_transactions})

    return parsed_data

def parse_time(time_str):
    date = str(time_str)
    if date.startswith("1900-01-01 "):
        date = date.replace("1900-01-01 ", "")
        date = date.replace(".", ":")
    date = ":".join(date.split(":")[-3:])
    return date

def is_filtered_ip(ip):
    filtered_ips = ['127.0.0.', '[::]', '91.198.115.', '162.218.65.', '209.222.252.']
    for filtered_ip in filtered_ips:
        if ip.startswith(filtered_ip):
            return True
    return False

def find_suspicious_transactions(parsed_data):
    onion_transactions = {}
    ip_transactions = {}
    suspicious_groups = {}

    for entry in parsed_data:
        peer = entry['Peer']
        if is_filtered_ip(peer):
            continue

        parsed_time = parse_time(entry['Time'])
        time = datetime.strptime(parsed_time, '%M:%S:%f')

        for transaction in entry['Transaktionen']:
            if ".onion" in peer:
                if transaction in onion_transactions:
                    prev_time = datetime.strptime(parse_time(onion_transactions[transaction]['Time']), '%M:%S:%f')
                    time_diff = abs(time - prev_time)
                    if time_diff <= timedelta(milliseconds=200):
                        if transaction not in suspicious_groups:
                            suspicious_groups[transaction] = {
                                'Transaction': transaction,
                                'First Network': onion_transactions[transaction]['Network'],
                                'First Time': parse_time(onion_transactions[transaction]['Time']),
                                'Second Network': 'Onion',
                                'Second Time': parsed_time,
                                'Time Difference': time_diff,
                                'Suspect Addresses': [onion_transactions[transaction]['Peer'], peer]
                            }
                        else:
                            suspicious_groups[transaction]['Suspect Addresses'].append(peer)
                else:
                    onion_transactions[transaction] = {'Peer': peer, 'Time': time, 'Network': 'Onion'}
            else:
                if transaction in ip_transactions:
                    prev_time = datetime.strptime(parse_time(ip_transactions[transaction]['Time']), '%M:%S:%f')
                    time_diff = abs(time - prev_time)
                    if time_diff <= timedelta(milliseconds=100):
                        if transaction not in suspicious_groups:
                            suspicious_groups[transaction] = {
                                'Transaction': transaction,
                                'First Network': ip_transactions[transaction]['Network'],
                                'First Time': parse_time(ip_transactions[transaction]['Time']),
                                'Second Network': 'IP',
                                'Second Time': parsed_time,
                                'Time Difference': time_diff,
                                'Suspect Addresses': [ip_transactions[transaction]['Peer'], peer]
                            }
                        else:
                            suspicious_groups[transaction]['Suspect Addresses'].append(peer)
                else:
                    ip_transactions[transaction] = {'Peer': peer, 'Time': time, 'Network': 'IP'}

    # Check and update suspect groups with mixed address types
    for transaction, group_info in suspicious_groups.items():
        suspect_addresses = group_info['Suspect Addresses']
        mixed_addresses = []
        time_diff_between_addresses = []

        prev_address_type = ".onion" if ".onion" in suspect_addresses[0] else "IP"
        for current_address in suspect_addresses[1:]:
            current_address_type = ".onion" if ".onion" in current_address else "IP"

            if prev_address_type != current_address_type:
                mixed_addresses.append(suspect_addresses[0])
                mixed_addresses.append(current_address)
                time_diff = group_info['Time Difference']
                time_diff_between_addresses.append((suspect_addresses[0], current_address, time_diff))
                break

            prev_address_type = current_address_type

        if mixed_addresses:
            group_info['Mixed Addresses'] = mixed_addresses
            if 'Mixed Addresses Details' not in group_info:
                group_info['Mixed Addresses Details'] = {}
            group_info['Mixed Addresses Details']['First Address Type'] = mixed_addresses[0]
            group_info['Mixed Addresses Details']['Second Address Type'] = mixed_addresses[1]
            group_info['Time Between Address Changes'] = time_diff_between_addresses

    return suspicious_groups

# Directory paths
input_directory = "../bitcoin-data/hashes/hash_saves"
output_directory = "../bitcoin-data/analysis/hashes"
suspect_addr_directory = "../bitcoin-data/analysis/suspect_addr"

# Get a list of all files in the input directory
input_files = [f for f in os.listdir(input_directory) if f.endswith("_incoming_hashes.log") and "-00-" not in f and "-55-" not in f]

# Load the list of checked files
checked_files_file = "../bitcoin-data/hashes/checked_hash_files.txt"
if os.path.exists(checked_files_file):
    with open(checked_files_file, "r") as checked_files:
        checked_files_list = checked_files.read().splitlines()
else:
    checked_files_list = []

log_file = open("../bitcoin-data/analysis/hashes/hashes_processing.log", "a")

pbar = tqdm(total=len(input_files), desc="Processing Files", unit="file")

for idx, file_name in enumerate(input_files, start=1):
    if file_name not in checked_files_list:
        file_path = os.path.join(input_directory, file_name)
        parsed_data = parse_data_file(file_path)
        suspicious_groups = find_suspicious_transactions(parsed_data)

        output_file_name = file_name.replace("_incoming_hashes.log", f"_{idx // 10:02d}.log")
        output_file_path = os.path.join(output_directory, output_file_name)

        with open(output_file_path, "a") as output_file:
            for transaction, group_info in suspicious_groups.items():
                output_file.write(f"Transaction: {group_info['Transaction']}\n")
                output_file.write(f"First Network: {group_info['First Network']}, Time: {group_info['First Time']}\n")
                output_file.write(f"Second Network: {group_info['Second Network']}, Time: {group_info['Second Time']}\n")
                output_file.write(f"Time Difference: {group_info['Time Difference']}\n")
                output_file.write(f"Suspect Addresses: {group_info['Suspect Addresses']}\n")

                if 'Mixed Addresses' in group_info:
                    output_file.write("-" * 80 + "\n")
                    mixed_addresses = group_info['Mixed Addresses']
                    mixed_addresses_details = group_info['Mixed Addresses Details']
                    output_file.write(f"Mixed Addresses: {mixed_addresses}\n")
                    output_file.write(f"First Address Type: {mixed_addresses_details['First Address Type']}\n")
                    output_file.write(f"Second Address Type: {mixed_addresses_details['Second Address Type']}\n")

                    if 'Time Between Address Changes' in group_info:
                        time_diff_between_addresses = group_info['Time Between Address Changes']
                        for address_change in time_diff_between_addresses:
                            output_file.write(f"Time Between {address_change[0]} and {address_change[1]}: {address_change[2]}\n")

                    mixed_addresses_str = f"{mixed_addresses[0]}; {mixed_addresses[1]}\n"
                    with open("../bitcoin-data/analysis/suspect_addr/hashes_sus.log", "a") as suspect_addr_file:
                        suspect_addr_file.write(mixed_addresses_str)

                output_file.write("=" * 80 + "\n\n")

        with open(checked_files_file, "a") as checked_files:
            checked_files.write(file_name + "\n")

        log_file.write(f"Processed: {file_name}\n")
        pbar.update(1)

        # Delete the processed file
        os.remove(file_path)

log_file.close()

