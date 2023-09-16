import requests
import json
from datetime import datetime
import os

API_URL = "https://bitnodes.io/api/v1/snapshots/"
SAVE_DIRECTORY = "../bitnodes"

def save_snapshot(url, timestamp, data):
    date = datetime.fromtimestamp(timestamp).strftime('%d_%m_%Y')
    filename = f"{date}_{timestamp}.json"
    filepath = os.path.join(SAVE_DIRECTORY, filename)
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Snapshot saved: {filepath}")

def fetch_bitnodes_data():
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        results = data['results']
        for result in results:
            url = result['url']
            timestamp = result['timestamp']
            response = requests.get(url)
            if response.status_code == 200:
                snapshot_data = response.json()
                save_snapshot(url, timestamp, snapshot_data)
            else:
                print(f"Error fetching snapshot data from URL: {url}. Status code: {response.status_code}")
    else:
        print(f"Error fetching bitnodes data. Status code: {response.status_code}")

def main():
    fetch_bitnodes_data()

if __name__ == '__main__':
    main()
