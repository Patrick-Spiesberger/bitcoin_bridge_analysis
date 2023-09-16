import os
import re
import subprocess
import filterPeers

def run_filter_peers(date):
    ipv4_path = "../bitcoin-data/daily_ipv4"
    ipv6_path = "../bitcoin-data/daily_ipv6"
    onion_path = "../bitcoin-data/daily_onion"

    # Validate the date format
    if not validate_date_format(date):
        print("Invalid date format.")
        return

    # Open the folders and get the addresses
    ipv4_addresses_with_port, ipv4_addresses_without_port = get_addresses(ipv4_path, date)
    ipv6_addresses_with_port, ipv6_addresses_without_port = get_addresses(ipv6_path, date)
    onion_addresses_with_port, onion_addresses_without_port = get_addresses(onion_path, date)

    # Print the number of addresses with the port
    print(f"Number of IPv4 addresses (with port): {len(ipv4_addresses_with_port)}")
    print(f"Number of IPv6 addresses (with port): {len(ipv6_addresses_with_port)}")
    print(f"Number of Onion addresses (with port): {len(onion_addresses_with_port)}")

    # Print the number of addresses without the port
    print(f"Number of IPv4 addresses (without port): {len(ipv4_addresses_without_port)}")
    print(f"Number of IPv6 addresses (without port): {len(ipv6_addresses_without_port)}")
    print(f"Number of Onion addresses (without port): {len(onion_addresses_without_port)}")


def validate_date_format(date):
    # Validate the date format
    try:
        day, month, year = date.split('-')
        int(day)
        int(month)
        int(year)
        return True
    except ValueError:
        return False


def extract_address_without_port(addr_with_port):
    # Extract address without the port
    return addr_with_port.split(':')[0]


def get_addresses(folder_path, date):
    addresses_with_port = []
    addresses_without_port = []
    file_path = os.path.join(folder_path, f"{date}.json")

    if not os.path.isfile(file_path):
        print(f"File {file_path} not found.")
        return addresses_with_port, addresses_without_port

    # Read the file and extract the "addr" field using regular expressions
    with open(file_path, 'r') as file:
        for line in file:
            addr_matches = re.findall(r'"addr":\s*"(.+?)"', line)
            for addr_match in addr_matches:
                addresses_with_port.append(addr_match)
                address_without_port = extract_address_without_port(addr_match)
                if address_without_port not in addresses_without_port:
                    addresses_without_port.append(address_without_port)

    return addresses_with_port, addresses_without_port


if __name__ == "__main__":
    while True:
        date = input("Enter the date (format: Day-Month-Year): ")
        if "quit" not in date:
            run_filter_peers(date)
            print(f"----------------------------")
        else:
            break
