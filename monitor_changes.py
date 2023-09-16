import os
import json
import subprocess
from datetime import datetime, timedelta

data_folder = '../bitcoin-data/daily_json_files/'
analysis_folder = '../bitcoin-data/analysis/changes/'

thresholds = {
    "services": 0,
    "relaytxes": 0,
    "lastsend": 0,
    "lastrecv": 0,
    "last_transaction": 0,
    "last_block": 0,
    "bytessent": 0,
    "bytesrecv": 0,
    "conntime": 0,
    "timeoffset": 0,
    "pingwait": 0,
    "version": 0,
    "inbound": 0,
    "bip152_hb_to": 0,
    "bip152_hb_from": 0,
    "startingheight": 0,
    "presynced_headers": 0,
    "synced_headers": 0,
    "synced_blocks": 0,
    "addr_processed": 0,
    "addr_rate_limited": 0,
    "minfeefilter": 0
}

def get_latest_data_file():
    json_files = sorted(os.listdir(data_folder), reverse=True)
    for filename in json_files:
        file_path = os.path.join(data_folder, filename)
        if is_file_within_last_days(file_path, 2):
            return file_path
    return None

def is_file_within_last_days(file_path, num_days):
    file_date_str = os.path.splitext(os.path.basename(file_path))[0]
    file_date = datetime.strptime(file_date_str, "%d-%m-%Y")
    days_ago = datetime.now() - timedelta(days=num_days)
    return file_date >= days_ago

def get_existing_addresses():
    existing_addresses = set()
    latest_data_file = get_latest_data_file()
    if latest_data_file:
        with open(latest_data_file, 'r') as file:
            try:
                data = json.load(file)
                for item in data:
                    if isinstance(item, dict) and 'addr' in item:
                        existing_addresses.add(item['addr'])
            except json.JSONDecodeError:
                pass
    #print("Existing Addresses:", existing_addresses)
    return existing_addresses

def check_peerinfo_changes(peerinfo, existing_addresses):
    timestamp = datetime.now().isoformat()
    for item in peerinfo:
        if isinstance(item, dict) and 'addr' in item:
            address = item['addr']
            if address in existing_addresses:
                existing_data = get_existing_data(address)
                if existing_data is not None and existing_data != item:
                    has_changes = False
                    for key, value in item.items():
                        if key in existing_data:
                            if isinstance(value, (int, float)):
                                threshold = thresholds.get(key, 0)
                                if abs(value - existing_data[key]) > threshold:
                                    has_changes = True
                                    break
                            else:
                                if value != existing_data[key]:
                                    has_changes = True
                                    break
                    if has_changes:
                        if not is_change_already_recorded(address, item):
                            output = {
                                'addr': address,
                                'time': timestamp,
                                'change_old': existing_data,
                                'change_new': item
                            }
                            save_analysis_file(output)

def get_existing_data(address):
    analysis_files = sorted(os.listdir(analysis_folder), reverse=True)
    for filename in analysis_files:
        file_path = os.path.join(analysis_folder, filename)
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                for item in data:
                    if isinstance(item, dict) and 'addr' in item and item['addr'] == address:
                        return item.get('change_new')
            except json.JSONDecodeError:
                pass
    return None

def is_change_already_recorded(address, item):
    analysis_files = sorted(os.listdir(analysis_folder), reverse=True)
    for filename in analysis_files:
        file_path = os.path.join(analysis_folder, filename)
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
                for existing_item in data:
                    if isinstance(existing_item, dict) and 'addr' in existing_item and existing_item['addr'] == address:
                        if existing_item.get('change_new') == item:
                            return True
            except json.JSONDecodeError:
                pass
    return False

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

def main():
    existing_addresses = get_existing_addresses()
    command_output = subprocess.check_output(['bitcoin-cli', 'getpeerinfo'])
    peerinfo = json.loads(command_output)
    check_peerinfo_changes(peerinfo, existing_addresses)

if __name__ == "__main__":
    main()
