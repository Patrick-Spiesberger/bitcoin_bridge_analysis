from datetime import datetime, timedelta
import re
from collections import Counter

def is_excluded_address(ip_address):
    excluded_prefixes = ['127.0.0.', '[::]', '91.198.115.', '162.218.65.', '209.222.252.']
    for prefix in excluded_prefixes:
        if ip_address.startswith(prefix):
            return True
    return False

def parse_log_file(log_file_path):
    ip_pattern = r'Peer connected: ((?:[0-9]{1,3}\.){3}[0-9]{1,3}|(?:[0-9a-zA-Z]+\.onion)):\d+'  # IPv4 and Onion

    ip_groups = {}
    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()
        for time_line, peer_line in zip(lines[::2], lines[1::2]):
            timestamp_match = re.search(r'Timestamp: (.+)', time_line)
            peer_match = re.search(ip_pattern, peer_line)
            if timestamp_match and peer_match:
                timestamp_str = timestamp_match.group(1).strip()
                ip_address = peer_match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %Y')
                except ValueError:
                    print(f'Error parsing timestamp: {timestamp_str}')
                    continue

                if not is_excluded_address(ip_address):
                    if ip_address not in ip_groups:
                        ip_groups[ip_address] = []
                    ip_groups[ip_address].append(timestamp)

    return ip_groups

def count_combinations(ip_groups, time_window):
    combinations_count = Counter()
    for ip_address, timestamps in ip_groups.items():
        for other_ip_address, other_timestamps in ip_groups.items():
            if ip_address != other_ip_address:
                for timestamp in timestamps:
                    for other_timestamp in other_timestamps:
                        if abs(timestamp - other_timestamp) <= time_window:
                            combination = tuple(sorted((ip_address, other_ip_address)))  # Sort the addresses in the tuple
                            combinations_count[combination] += 1

    return combinations_count

def write_combinations_count_to_file(combinations_count, count_file_path, ip_groups):
    with open(count_file_path, 'w') as count_file:
        count_file.write("Address combinations count:\n")
        for combination, count in sorted(combinations_count.items(), key=lambda x: (-x[1], min(abs(timestamp - other_timestamp) for timestamp in ip_groups[x[0][0]] for other_timestamp in ip_groups[x[0][1]]))):
            count //= 2  # Divide the count by two since the combinations are counted twice
            time_diff = min(abs(timestamp - other_timestamp) for timestamp in ip_groups[combination[0]]
                            for other_timestamp in ip_groups[combination[1]])
            count_file.write(f"{combination[0]} related to {combination[1]} (Count: {count}, Time Difference: {time_diff})\n")

def write_suspect_peer_addresses_to_file(combinations_count, peer_file_path, ip_groups):
    with open(peer_file_path, 'w') as peer_file:
        for combination, count in sorted(combinations_count.items(), key=lambda x: (-x[1], min(abs(timestamp - other_timestamp) for timestamp in ip_groups[x[0][0]] for other_timestamp in ip_groups[x[0][1]]))):
            for _ in range(count // 2):
                peer_file.write(f"{combination[0]}; {combination[1]}\n")

def main():
    log_file_path = '../bitcoin-data/peer_connect.log'
    count_file_path = '../bitcoin-data/analysis/detail/connect_count.log'
    peer_file_path = '../bitcoin-data/analysis/suspect_addr/connect_sus.log'

    time_window = timedelta(seconds=10)

    ip_groups = parse_log_file(log_file_path)
    combinations_count = count_combinations(ip_groups, time_window)

    if not combinations_count:
        print("No address combinations found.")
    else:
        print("Address combinations count (sorted by count in descending order):")
        for combination, count in sorted(combinations_count.items(), key=lambda x: (-x[1], min(abs(timestamp - other_timestamp) for timestamp in ip_groups[x[0][0]] for other_timestamp in ip_groups[x[0][1]]))):
            count //= 2  # Divide the count by two since the combinations are counted twice
            time_diff = min(abs(timestamp - other_timestamp) for timestamp in ip_groups[combination[0]]
                            for other_timestamp in ip_groups[combination[1]])
            print(f"{combination[0]} related to {combination[1]} (Count: {count}, Time Difference: {time_diff})")

    if combinations_count:
        write_combinations_count_to_file(combinations_count, count_file_path, ip_groups)
        write_suspect_peer_addresses_to_file(combinations_count, peer_file_path, ip_groups)

if __name__ == "__main__":
    main()
