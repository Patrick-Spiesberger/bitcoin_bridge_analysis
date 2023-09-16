import os
import shutil
import datetime

def main():
    log_file_path = '../bitcoin-data/analysis/ping/heartbeat.log'
    save_folder = '../bitcoin-data/analysis/ping/pinglogs'
    max_file_size_mb = 30

    if not os.path.exists(save_folder):
        os.mkdir(save_folder)

    file_size_mb = os.path.getsize(log_file_path) / (1024 * 1024)

    if file_size_mb > max_file_size_mb:
        now = datetime.datetime.now()
        timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
        new_file_name = f"{timestamp}_ping_anomaly.log"

        destination_path = os.path.join(save_folder, new_file_name)

        shutil.copy(log_file_path, destination_path)

        open(log_file_path, 'w').close()

        print(f"File saved in {destination_path}.")

if __name__ == "__main__":
    main()
