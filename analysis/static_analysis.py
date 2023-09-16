import os
import re

def get_newest_file(path):
    files = os.listdir(path)
    if not files:
        return None
    
    newest_file = max(files, key=lambda f: os.path.getctime(os.path.join(path, f)))
    return os.path.join(path, newest_file)

def is_suspicious_address(addr):
    suspicious_prefixes = ['127.0.0.', '[::]', '91.198.115.', '162.218.65.', '209.222.252.']
    for prefix in suspicious_prefixes:
        if addr.startswith(prefix):
            return False
    return True

def analyze_changes(file_path, output_file, suspect_output_file):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    address_changes = {}  # Dictionary to store address changes
    address_pair_counts = {}  # Dictionary to store address pair occurrence counts
    
    output_lines = []  # List to store detailed output
    suspect_output_lines = []
    
    for line in lines:
        match = re.search(r'{"addr": "(.*?)", "date": "(.*?)", "changes": ({.*?})}', line)
        if match:
            addr = match.group(1)
            date = match.group(2)
            changes_str = match.group(3)
            
            if is_suspicious_address(addr):
                if changes_str in address_changes:
                    prev_addr = address_changes[changes_str]
                    address_pair = f"{prev_addr}; {addr}"
                    changes = re.findall(r'"(.*?)": ({.*?})', changes_str)
                    
                    if prev_addr != addr:  # Filter out identical addresses
                        if address_pair in address_pair_counts:
                            address_pair_counts[address_pair] += 1
                        else:
                            address_pair_counts[address_pair] = 1

                        output_lines.append(address_pair)
                        output_lines.append(f"Date: {date}")
                        output_lines.append("Common Changes:")
                        for key, value in changes:
                            output_lines.append(f"    {key}: {value}")
                        output_lines.append('-' * 80)

                        suspect_output_lines.append(address_pair)
    
                address_changes[changes_str] = addr
    
    sorted_pairs = sorted(address_pair_counts.items(), key=lambda x: x[1], reverse=True)
    
    output_lines.append("\n\n\n")
    output_lines.append("Summary of Suspicious Address Pairs (Sorted by Frequency):")
    output_lines.append('-' * 80)
    for address_pair, count in sorted_pairs:
        output_lines.append(address_pair)
        output_lines.append(f"Occurrences: {count}")
        output_lines.append('-' * 80)
    
    # Save detailed output to the specified file
    with open(output_file, 'w') as output_f:
        output_f.write('\n'.join(output_lines))
    
    # Save unique suspect address pairs to the specified file
    with open(suspect_output_file, 'w') as suspect_output_f:
        suspect_output_f.write('\n'.join(suspect_output_lines))

if __name__ == "__main__":
    data_path = "../bitcoin-data/analysis/changes"
    output_path = "../bitcoin-data/analysis/detail"
    suspect_output_path = "../bitcoin-data/analysis/suspect_addr"
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    if not os.path.exists(suspect_output_path):
        os.makedirs(suspect_output_path)
    
    newest_file_path = get_newest_file(data_path)
    output_file_path = os.path.join(output_path, "static_analysis_output.log")
    suspect_output_file_path = os.path.join(suspect_output_path, "static_sus.log")
    
    print(f"Please ensure that search_static_changes.py is executed before")

    if newest_file_path:
        print(f"Analyzing the newest file: {newest_file_path}")
        analyze_changes(newest_file_path, output_file_path, suspect_output_file_path)
        print(f"Analysis results saved to: {output_file_path}")
        print(f"Suspect address pairs saved to: {suspect_output_file_path}")
    else:
        print("No files found in the specified directory.")
