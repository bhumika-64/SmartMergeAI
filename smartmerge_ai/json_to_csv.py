import json
import csv
 
# Function to convert JSON to CSV
def json_to_csv(json_file, csv_file):
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
 
    # Extract headers from keys (assuming all PRs have the same keys)
    if len(data) == 0:
        print("No data found in JSON file.")
        return
 
    headers = data[0].keys()  # Get keys from the first dictionary
 
    # Write to CSV file
    with open(csv_file, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()  # Write header
        writer.writerows(data)  # Write 
 
    print(f"JSON converted to CSV and saved as: {csv_file}")
 
# Convert Closed PRs
json_to_csv("data/raw/closed_pr/wheel_all_closed_prs.json", "data/raw/closed_pr/wheel_all_closed_prs.csv")
 
# Convert Open PRs
json_to_csv("data/raw/open_pr/wheel_all_open_prs.json", "data/raw/open_pr/wheel_all_open_prs.csv")