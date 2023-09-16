import os
import json
from datetime import datetime, timedelta

data_folder = '../bitcoin-data/daily_json_files/'
analysis_folder = '../bitcoin-data/analysis/changes/'

# Liste der zusätzlichen Attribute, die verglichen werden sollen
additional_attributes = [
    "services",
    "servicenames",
    "relaytxes",
    "subvers",
    "bip152_hb_to",
    "bip152_hb_from",
    "startingheight",
    "presynced_headers",
    "synced_headers",
    "synced_blocks",
    "addr_relay_enabled",
   # "addr_processed",
    "addr_rate_limited",
    "minfeefilter",
   # "pingtime",
   # "minping",
    "version"
]

# Schwellenwerte für die prozentuale Änderung
thresholds = {
   #  "lastsend": 0.05,
   #  "lastrecv": 0.05,
    "bytessent": 0.0,
    "bytesrecv": 0.0,
    "conntime": 0.0,
    "pingtime": 1.0,
    "minping": 1.0,
    "version": 0,
    "startingheight": 0,
    "minfeefilter": 0.0,
    "synced_headers": 0.1,
    "synced_blocks": 0.1
}

start_date = "27-06-2023"

def get_existing_addresses():
    existing_addresses = set()
    analysis_files = os.listdir(analysis_folder)
    for filename in analysis_files:
        file_path = os.path.join(analysis_folder, filename)
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                for item in data:
                    existing_addresses.add(item['addr'])
            except json.JSONDecodeError:
                pass
    return existing_addresses

def process_json_file(file_path, existing_addresses):
    filename = os.path.basename(file_path)
    current_date_str = filename.split(".")[0]
    current_date = datetime.strptime(current_date_str, "%d-%m-%Y")
    prev_date = current_date - timedelta(days=1)
    prev_date_str = prev_date.strftime("%d-%m-%Y")

    prev_file_path = os.path.join(data_folder, f"{prev_date_str}.json")

    if not os.path.exists(prev_file_path):
        print(f"No previous file found for {prev_date_str}. Skipping...")
        return

    print(f"Processing {filename}...")
    with open(file_path, 'r') as file:
        current_data = json.load(file)
    
    with open(prev_file_path, 'r') as prev_file:
        prev_data = json.load(prev_file)
    
    all_addresses = set(item['addr'] for item in current_data) | set(item['addr'] for item in prev_data)

    for address in all_addresses:
        current_item = next((item for item in current_data if item['addr'] == address), None)
        prev_item = next((item for item in prev_data if item['addr'] == address), None)
        check_address_changes(address, current_item, prev_item, current_date_str)

def check_address_changes(address, current_item, prev_item, current_date):
    if current_item and prev_item:
        has_change = False
        changes = {}
        for key in additional_attributes:
            if key in current_item and key in prev_item:
                current_value = convert_to_numeric(current_item[key])
                existing_value = convert_to_numeric(prev_item[key])
                threshold = thresholds.get(key, 0.0)
                if existing_value != 0:
                    percent_change = abs((current_value - existing_value) / existing_value)
                    if percent_change > threshold:
                        has_change = True
                        changes[key] = {
                            'old_value': existing_value,
                            'new_value': current_value,
                            'percent_change': percent_change
                        }
                        print(f"Change detected for Address: {address}, Field: {key}, "
                              f"Old Value: {existing_value}, New Value: {current_value}, "
                              f"Percent Change: {percent_change * 100:.2f}%")

        if has_change:
            #timestamp = datetime.now().isoformat()
            output = {
                'addr': address,
                'date': current_date,
                'changes': changes
            }
            save_analysis_file(output)

def convert_to_numeric(value):
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return 0

def save_analysis_file(output):
    timestamp = datetime.now().strftime('%d-%m-%Y')
    file_name = f"{timestamp}.json"
    file_path = os.path.join(analysis_folder, file_name)
    with open(file_path, 'a+') as file:
        file.seek(0)
        data = file.read()
        if len(data) > 0:
            file.write(',')
        json.dump(output, file)
        file.write('\n')

def is_file_after_start_date(filename, start_date):
    file_date_str = filename.split(".")[0]
    file_date = datetime.strptime(file_date_str, "%d-%m-%Y")
    start_date = datetime.strptime(start_date, "%d-%m-%Y")
    return file_date >= start_date

def main():
    existing_addresses = get_existing_addresses()
    json_files = os.listdir(data_folder)
    for filename in json_files:
        if is_file_after_start_date(filename, start_date):
            file_path = os.path.join(data_folder, filename)
            process_json_file(file_path, existing_addresses)

if __name__ == "__main__":
    main()

