import os
import json
from datetime import datetime
from tqdm import tqdm

# Funktion, um die Adresse aus der JSON-Datei abzurufen
def get_address_from_json(json_file, peer_id):
    with open(json_file, 'r') as f:
        data = json.load(f)
        for peer_info in data:
            if peer_info.get('id') == peer_id:
                return peer_info.get('addr')
    return None

def main():
    # Pfad zum Log-Datei
    log_file_path = '../bitcoin-data/peer_disconnect.log'

    # Pfad zum Verzeichnis mit den JSON-Dateien
    json_files_dir = '../bitcoin-data/daily_json_files/'

    # Pfad zur neuen Log-Datei
    new_log_file_path = '../bitcoin-data/peer_disconnect_addr.log'

    # Zähler für den Fortschritt
    total_lines = sum(1 for line in open(log_file_path))
    progress_bar = tqdm(total=total_lines, desc="Processing", unit=" lines")

    # Lesen und Bearbeiten der Log-Datei und Schreiben in die neue Datei
    with open(log_file_path, 'r') as log_file, open(new_log_file_path, 'a') as new_log_file:
        log_lines = log_file.readlines()
        for i in range(0, len(log_lines), 2):
            timestamp_line = log_lines[i].strip()
            peer_id_line = log_lines[i + 1].strip()

            try:
                peer_id = int(peer_id_line.split(': ')[1])

                timestamp = ' '.join(timestamp_line.split(' ')[1:])
                timestamp_format = "%a %b %d %H:%M:%S %Y"
                date_time_obj = datetime.strptime(timestamp, timestamp_format)

                day = date_time_obj.strftime("%d")
                month = date_time_obj.strftime("%m")
                year = date_time_obj.strftime("%Y")
                json_file_path = os.path.join(json_files_dir, f"{day}-{month}-{year}.json")

                address = get_address_from_json(json_file_path, peer_id)

                if address is not None:
                    new_log_file.write(f"{timestamp_line}\nPeer disconnected: {address}\n")

            except (ValueError, IndexError, FileNotFoundError, json.JSONDecodeError, Exception) as e:
                # Wenn eine Exception auftritt, wird der Eintrag übersprungen
                print(f"Exception while processing: {timestamp_line}\nError: {e}")

            progress_bar.update(2)

    progress_bar.close()

    os.remove(log_file_path)

if __name__ == "__main__":
    main()
