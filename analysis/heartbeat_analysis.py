import os
from collections import defaultdict
from datetime import datetime
from tqdm import tqdm

def is_onion(address):
    return ".onion" in address

def parse_log_file(file_path):
    excluded_prefixes = ['127.0.0.', '[::]', '91.198.115.', '162.218.65.', '209.222.252.']
    data = defaultdict(list)
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("20"):
                date = datetime.strptime(line.strip(), "%Y-%m-%d %H:%M:%S")
            if line.startswith("Anomaly:"):
                parts = line.strip().split('; ')
                address_info = parts[0].split(' ', 1)[1]
                address = address_info.split('for ')[1]
                if any(address.startswith(prefix) for prefix in excluded_prefixes):
                    continue
                elements = parts[1].split(', ')
                old_ping = float(elements[0].split('Old Ping: ')[1])
                new_ping = float(elements[1].split('New Ping: ')[1])
                changes = float(elements[2].split('Changes: ')[1])
                data[date].append((address, old_ping, new_ping, changes))
    return data

def calculate_ping_similarity(old_ping1, new_ping1, old_ping2, new_ping2, threshold=0.15):
    return abs(old_ping1 - old_ping2) <= threshold and abs(new_ping1 - new_ping2) <= threshold

def main():
    log_files_directory = '../bitcoin-data/analysis/ping/pinglogs/'
    processed_files_file = '../bitcoin-data/analysis/ping/processed_files.log'
    detail_output_directory = '../bitcoin-data/analysis/detail/ping/'
    
    processed_files = set()
    if os.path.exists(processed_files_file):
        with open(processed_files_file, 'r') as f:
            processed_files = set(line.strip() for line in f.readlines())
    
    for file_name in os.listdir(log_files_directory):
        if file_name.endswith('.log') and file_name not in processed_files:
            log_file_path = os.path.join(log_files_directory, file_name)
            data = parse_log_file(log_file_path)
            
            total_entries = sum(len(entries) for entries in data.values())
            
            progress_bar = tqdm(total=total_entries, desc=f"Processing {file_name}", dynamic_ncols=True)
            
            detail_output_path = os.path.join(detail_output_directory, f"{os.path.splitext(file_name)[0]}_detail.log")
            
            with open('../bitcoin-data/analysis/suspect_addr/ping_sus.log', 'a') as output_file, \
                    open(detail_output_path, 'a') as detail_output_file:
                for date, entries in data.items():
                    ip_onion_pairs = []
                    for i, (address1, old1, new1, changes1) in enumerate(entries):
                        for j in range(i + 1, len(entries)):
                            address2, old2, new2, changes2 = entries[j]
                            #if is_onion(address1) != is_onion(address2) and date == list(data.keys())[0]:
                            #    ip_onion_pairs.append(((address1, old1, new1, changes1), (address2, old2, new2, changes2)))
                            if date == list(data.keys())[0] and calculate_ping_similarity(old1, new1, old2, new2):
                                if (abs(changes1 - changes2) <= 0.1):
                                    output_file.write(f"{address1}; {address2}\n")
                                    detail_output_file.write(f"Address 1: {address1}\n")
                                    detail_output_file.write(f"Old Ping 1: {old1:.6f}\n")
                                    detail_output_file.write(f"New Ping 1: {new1:.6f}\n")
                                    detail_output_file.write(f"Address 2: {address2}\n")
                                    detail_output_file.write(f"Old Ping 2: {old2:.6f}\n")
                                    detail_output_file.write(f"New Ping 2: {new2:.6f}\n")
                                    detail_output_file.write(f"Time: {date}\n")
                                    detail_output_file.write(f"Change Difference: {abs(changes2 - changes1):.6f}\n\n")
                            progress_bar.update(1)
                        
                    # Write IP and Onion pairs at the beginning of the detail output file
                    # for ip_pair, onion_pair in ip_onion_pairs:
                    #    output_file.write(f"{ip_pair[0]}; {onion_pair[0]}\n")
                    #    detail_output_file.write(f"Address 1: {ip_pair[0]}\n")
                    #    detail_output_file.write(f"Old Ping 1: {ip_pair[1]:.6f}\n")
                    #    detail_output_file.write(f"New Ping 1: {ip_pair[2]:.6f}\n")
                    #    detail_output_file.write(f"Address 2: {onion_pair[0]}\n")
                    #    detail_output_file.write(f"Old Ping 2: {onion_pair[1]:.6f}\n")
                    #    detail_output_file.write(f"New Ping 2: {onion_pair[2]:.6f}\n")
                    #    detail_output_file.write(f"Time: {date}\n")
                    #    detail_output_file.write(f"Change Difference: {abs(onion_pair[3] - ip_pair[3]):.6f}\n\n")
            
            progress_bar.close()
            
            processed_files.add(file_name)
            with open(processed_files_file, 'a') as f:
                f.write(f"{file_name}\n")

if __name__ == "__main__":
    main()
