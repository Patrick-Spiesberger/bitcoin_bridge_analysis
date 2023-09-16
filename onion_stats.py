import os
import json
from datetime import date
from statistics import mean, median

daily_folder = '../bitcoin-data/daily_onion'
stats_folder = '../bitcoin-data/analysis/stats/onion'

# Check if statistics are already calculated for all days
def is_stats_complete(stats_folder):
    today = date.today().strftime('%d-%m-%Y')
    file_list = [file_name for file_name in os.listdir(stats_folder) if file_name.endswith('.json')]

    return len(file_list) > 0 and today + '.json' in file_list

# Function to convert the numerical version number to its corresponding string representation
def convert_version(version_num):
    major = version_num // 10000
    minor = (version_num // 100) % 100
    patch = version_num % 100
    return f"v{major}.{minor}.{patch}"

# Calculate daily statistics for a given file
def calculate_daily_stats(file_path):
    date_str = os.path.basename(file_path).split('.')[0]
    with open(file_path) as file:
        data = json.load(file)

    if not data:
        return None

    stats = {}

    for key in data[0].keys():
        if isinstance(data[0][key], (int, float)):
            values = [entry[key] for entry in data if key in entry and isinstance(entry[key], (int, float))]

            if values:
                avg = mean(values)
                med = median(values)
                stats[key] = {
                    'mean': avg,
                    'median': med,
                    'count_peers': len(set([entry['id'] for entry in data if key in entry]))  # Number of peers that have this field
                }

        elif isinstance(data[0][key], dict):  # For dictionaries (sub-elements)
            sub_stats = {}
            for sub_key in data[0][key].keys():
                sub_values = [entry[key][sub_key] for entry in data if key in entry and sub_key in entry[key] and isinstance(entry[key][sub_key], (int, float))]
                if sub_values:
                    sub_avg = mean(sub_values)
                    sub_med = median(sub_values)
                    sub_stats[sub_key] = {
                        'mean': sub_avg,
                        'median': sub_med,
                        'count_peers': len(set([entry['id'] for entry in data if key in entry and sub_key in entry[key]]))
                    }
            if sub_stats:
                stats[key] = sub_stats

    return {'date': date_str, 'stats': stats}


# Calculate general statistics for all files
def calculate_general_stats(file_list):
    general_stats = {}

    for file_path in file_list:
        with open(file_path) as file:
            data = json.load(file)

        if not data:
            continue

        for key in data[0].keys():
            if isinstance(data[0][key], (int, float)):
                values = [entry[key] for entry in data if key in entry and isinstance(entry[key], (int, float))]

                if values:
                    avg = mean(values)
                    med = median(values)
                    if key not in general_stats:
                        general_stats[key] = {
                            'sum': avg,
                            'count': len(values),
                            'mean': avg,
                            'median': med,
                            'count_peers': len(set([entry['id'] for entry in data if key in entry]))
                        }
                    else:
                        general_stats[key]['sum'] += avg
                        general_stats[key]['count'] += len(values)
                        general_stats[key]['mean'] = general_stats[key]['sum'] / general_stats[key]['count']
                        general_stats[key]['median'] = med
                        general_stats[key]['count_peers'] = len(set([entry['id'] for entry in data if key in entry]))

            elif isinstance(data[0][key], dict):  # For dictionaries (sub-elements)
                for sub_key in data[0][key].keys():
                    sub_values = [entry[key][sub_key] for entry in data if key in entry and sub_key in entry[key] and isinstance(entry[key][sub_key], (int, float))]
                    if sub_values:
                        sub_avg = mean(sub_values)
                        sub_med = median(sub_values)
                        if key not in general_stats:
                            general_stats[key] = {
                                sub_key: {
                                    'sum': sub_avg,
                                    'count': len(sub_values),
                                    'mean': sub_avg,
                                    'median': sub_med,
                                    'count_peers': len(set([entry['id'] for entry in data if key in entry and sub_key in entry[key]]))
                                }
                            }
                        else:
                            if sub_key not in general_stats[key]:
                                general_stats[key][sub_key] = {
                                    'sum': sub_avg,
                                    'count': len(sub_values),
                                    'mean': sub_avg,
                                    'median': sub_med,
                                    'count_peers': len(set([entry['id'] for entry in data if key in entry and sub_key in entry[key]]))
                                }
                            else:
                                general_stats[key][sub_key]['sum'] += sub_avg
                                general_stats[key][sub_key]['count'] += len(sub_values)
                                general_stats[key][sub_key]['mean'] = general_stats[key][sub_key]['sum'] / general_stats[key][sub_key]['count']
                                general_stats[key][sub_key]['median'] = sub_med
                                general_stats[key][sub_key]['count_peers'] = len(set([entry['id'] for entry in data if key in entry and sub_key in entry[key]]))

    return general_stats

# List of found files in the daily_onion folder
file_list = [os.path.join(daily_folder, file_name) for file_name in os.listdir(daily_folder)]

# Check if statistics are already calculated for all days
if not is_stats_complete(stats_folder):
    if file_list:
        # Create daily statistics
        daily_stats = []
        for file_path in file_list:
            daily_stat = calculate_daily_stats(file_path)
            if daily_stat:
                daily_stats.append(daily_stat)

        # Create general statistics
        general_stats = calculate_general_stats(file_list)

        # Save daily statistics
        for daily_stat in daily_stats:
            file_name = daily_stat['date'] + '.json'
            file_path = os.path.join(stats_folder, file_name)
            with open(file_path, 'w') as file:
                json.dump(daily_stat, file, indent=4)

        # Save general statistics
        with open(os.path.join(stats_folder, 'general.json'), 'w') as file:
            json.dump(general_stats, file, indent=4)

    else:
        print("No daily files found.")

else:
    print("Statistics are already complete for all days.")
