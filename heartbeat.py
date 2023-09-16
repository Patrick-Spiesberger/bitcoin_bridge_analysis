import subprocess
import time
import json
import random
from datetime import datetime

# Anpassbare Variablen
PING_INTERVAL = 10  # Zeit zwischen Pings in Sekunden
CHECK_INTERVAL_LOWER = 15  # Untere Grenze des Zeitintervalls zwischen den Durchläufen in Sekunden
CHECK_INTERVAL_UPPER = 25  # Obere Grenze des Zeitintervalls zwischen den Durchläufen in Sekunden
LOG_FILE = '../bitcoin-data/analysis/ping/heartbeat.log'  # Speicherort der Log-Datei
PING_THRESHOLD = 0.30  # Schwellenwert für die Anomalieerkennung (30% Änderung)

def calculate_percentage_difference(old_value, new_value):
    if old_value == 0:
        return float('inf') if new_value != 0 else 0.0

    return ((new_value - old_value) / abs(old_value)) * 100.0

def get_peer_info():
    command = 'bitcoin-cli getpeerinfo'
    result = subprocess.check_output(command.split()).decode('utf-8')
    return json.loads(result)

def ping_addresses():
    command = f'bitcoin-cli ping'
    subprocess.run(command.split())

def check_ping_changes(old_peers, new_peers):
    log = []
    for old_peer in old_peers:
        old_ping = old_peer.get("pingtime", -1)
        new_ping = next((new_peer.get("pingtime", -1) for new_peer in new_peers if new_peer["addr"] == old_peer["addr"]), -1)
        if old_ping != -1 and new_ping != -1 and abs(new_ping - old_ping) / old_ping > PING_THRESHOLD:
            changes = abs(new_ping - old_ping) / old_ping
            log.append(f'Anomaly: Ping time change for {old_peer["addr"]}; Old Ping: {old_ping}, New Ping: {new_ping}, Changes: {changes}')
    return log

def check_new_peers(old_peers, new_peers):
    log = []
    old_addresses = set(peer["addr"] for peer in old_peers)
    new_addresses = set(peer["addr"] for peer in new_peers)
    added_peers = new_addresses - old_addresses
    removed_peers = old_addresses - new_addresses

    if added_peers:
        log.append(f'New peers detected: {", ".join(added_peers)}')
    if removed_peers:
        log.append(f'Peers removed: {", ".join(removed_peers)}')

    return log

def write_to_log(log):
    if log:
        with open(LOG_FILE, 'a') as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f'{timestamp}\n' + '\n'.join(log) + '\n')

if __name__ == "__main__":
    while True:
        try:
            print("Getting peer info...")
            old_peers = get_peer_info()
            ping_addresses()
            print("Ping sent to all addresses. Waiting for 10 seconds...")
            time.sleep(PING_INTERVAL)

            new_peers = get_peer_info()

            ping_log = check_ping_changes(old_peers, new_peers)
            new_peer_log = check_new_peers(old_peers, new_peers)

            log = ping_log + new_peer_log

            if log:
                print("\n=== Log ===")
                for entry in log:
                    print(entry)
                print("============")

            write_to_log(log)
        except Exception as e:
            print(f"Error occurred: {e}")

        # Generate a random time interval between CHECK_INTERVAL_LOWER and CHECK_INTERVAL_UPPER seconds
        random_interval = random.randint(CHECK_INTERVAL_LOWER, CHECK_INTERVAL_UPPER)
        print(f"Next check in {random_interval} seconds...")
        time.sleep(random_interval)
