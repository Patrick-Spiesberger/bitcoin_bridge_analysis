import os
from collections import Counter
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def extract_subver_values(file_path):
    with open(file_path, "r") as file:
        contents = file.read()
        return re.findall(r'"subver": "([^"]+)"', contents)

def get_unique_addresses(file_path):
    with open(file_path, "r") as file:
        contents = file.read()
        return set(re.findall(r'"addr": "([^"]+)"', contents))

def get_top_n_subver(subver_values, n):
    subver_count = Counter(subver_values)
    top_subver = subver_count.most_common(n)
    return top_subver

def create_bar_chart(data, title, output_path):
    subvers, counts = zip(*data)
    plt.figure(figsize=(10, 6))
    plt.bar(subvers, counts)
    plt.title(title)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def is_address_excluded(ip_address):
    excluded_subnets = ["127.0.0"] 
    ip_parts = ip_address.split(":")
    ip = ip_parts[0]  # Use only the IP part, ignore the port if present
    for subnet in excluded_subnets:
        if ip in subnet:
            return True
    return False

def main():
    input_directory = "../bitcoin-data/"
    output_directory = "../bitcoin-data/analysis/graphs/"
    categories = ["ipv4", "ipv6", "onion"]
    top_n = 10

    # Get the date of the second newest file
    now = datetime.now()
    second_newest_date = now - timedelta(days=1)
    second_newest_date_str = second_newest_date.strftime("%d-%m-%Y")

    all_addresses = set()

    for category in categories:
        file_paths = [os.path.join(input_directory, f"daily_{category}", file_name) for file_name in os.listdir(os.path.join(input_directory, f"daily_{category}"))]

        # Filter the file paths to include only the second newest date file and older
        file_paths_vortag = [file_path for file_path in file_paths if second_newest_date_str in file_path]

        if len(file_paths_vortag) == 0:
            print(f"No data available for {category.upper()} Peers on {second_newest_date_str}")
            continue

        all_subver_values = []

        for file_path in file_paths_vortag:  # Only consider the second newest date file and older
            date_str = os.path.splitext(os.path.basename(file_path))[0]  # Extract the date part from the filename
            subver_values = extract_subver_values(file_path)
            all_subver_values.extend(subver_values)

            # Get unique addresses from the current file
            addresses = get_unique_addresses(file_path)

            # Filter excluded addresses
            addresses = [address for address in addresses if not is_address_excluded(address)]
            all_addresses.update(addresses)

        top_subver = get_top_n_subver(all_subver_values, top_n)

        print(f"Top {top_n} subver values for {category.upper()} Peers on {second_newest_date_str}:")
        for subver, count in top_subver:
            print(f"{subver}: {count}")

        data = [(subver, count) for subver, count in top_subver]
        title = f"Top {top_n} subver values for {category.upper()} Peers on {second_newest_date_str}"
        output_path = os.path.join(output_directory, f"{category}_subver_distribution_{second_newest_date_str}.png")

        create_bar_chart(data, title, output_path)

    unique_address_count = len(all_addresses)
    print(f"Total number of unique addresses on {second_newest_date_str} (excluding excluded subnets): {unique_address_count}")

if __name__ == "__main__":
    main()
