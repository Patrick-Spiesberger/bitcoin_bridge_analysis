import subprocess
import json
import datetime
import os

def get_mempool_entries():
    # Execute the command `bitcoin-cli getrawmempool true` and retrieve the mempool entries
    command = 'bitcoin-cli getrawmempool true'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        mempool_hashes = json.loads(result.stdout)
        mempool_entries = []
        limit = 100
        mempool_hashes_list = list(mempool_hashes)
        for hash_value in mempool_hashes_list[:limit]:
            entry_command = f'bitcoin-cli getmempoolentry {hash_value}'
            entry_result = subprocess.run(entry_command, shell=True, capture_output=True, text=True)
            if entry_result.returncode == 0:
                entry_info = json.loads(entry_result.stdout)
                mempool_entries.append(entry_info)
        return mempool_entries
    else:
        print('Error retrieving mempool entries:')
        print(result.stderr)

def write_to_json(mempool_entries):
    # Create the directory if it doesn't exist
    directory = '../bitcoin-data/daily_mempool_info'
    os.makedirs(directory, exist_ok=True)

    # Write the mempool entries to a JSON file
    timestamp = datetime.datetime.now().strftime('%d-%m-%Y')
    filename = f'{directory}/mempool_entries_{timestamp}.json'

    if os.path.exists(filename):
        with open(filename, 'r') as file:
            existing_data = json.load(file)
        existing_data.extend(mempool_entries)
        mempool_entries = existing_data

    with open(filename, 'w') as file:
        json.dump(mempool_entries, file, indent=4)
    print(f'Mempool entries saved in {filename}.')

# Main program
mempool_entries = get_mempool_entries()
if mempool_entries:
    write_to_json(mempool_entries)
