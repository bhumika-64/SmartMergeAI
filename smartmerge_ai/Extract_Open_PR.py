# 🔄 Cleans & structures PR data for RAG
import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
import pytz
 
# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
 
if not GITHUB_TOKEN:
    raise ValueError(
        "GitHub token not found. Ensure .env file has GITHUB_TOKEN set.")
 
BASE_URL = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
 
 
def check_rate_limit():
    """Check GitHub API rate limits before making further requests."""
    url = f"{BASE_URL}/rate_limit"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        rate_limit = response.json()["rate"]
        remaining = rate_limit["remaining"]
        reset_time = datetime.fromtimestamp(
            rate_limit["reset"], tz=pytz.UTC).strftime('%Y-%m-%d %H:%M:%S')
        print(
            f"GitHub API Rate Limit: {remaining} requests left. Resets at {reset_time}.")
        if remaining < 10:
            print(" Nearing rate limit! Waiting for reset...")
            time.sleep(60)  # Wait 1 minute before retrying
    else:
        print(" Failed to fetch rate limit. Proceeding with caution.")
 
 
def fetch_file_changes(pr_number, repo_owner, repo_name):
    """Fetches all file changes in a PR, including added, modified, deleted files and their diffs."""
    url = f"{BASE_URL}/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)
 
    if response.status_code != 200:
        print(
            f"Error fetching file changes for PR #{pr_number}: {response.json()}")
        return []
 
    file_changes = []
    for file in response.json():
        filename = file["filename"]
        status = file["status"]  # added, modified, removed
        patch = file.get("patch", "")  # Full patch/diff if available
 
        added_lines = []
        removed_lines = []
        patch_lines = patch.split("\n") if patch else []
 
        for line in patch_lines:
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line)
            elif line.startswith("-") and not line.startswith("---"):
                removed_lines.append(line)
 
        file_changes.append({
            "Filename": filename,
            "Status": status,
            "Added Lines": added_lines,
            "Removed Lines": removed_lines,
            "Full Diff": patch_lines
        })
 
    return file_changes
 
 
def fetch_pr_comments(pr_number, repo_owner, repo_name):
    """Fetches all comments on a PR and categorizes them as old or new."""
    url = f"{BASE_URL}/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(
            f"Error fetching comments for PR #{pr_number}: {response.json()}")
        return {"Old Comments": [], "New Comments": []}
 
    comments = response.json()
    comments.sort(key=lambda x: x["created_at"])  # Sort by creation time
    midpoint = len(comments) // 2
 
    old_comments = [{
        "User": comment["user"]["login"],
        "Created At": comment["created_at"],
        "Body": comment["body"]
    } for comment in comments[:midpoint]]
 
    new_comments = [{
        "User": comment["user"]["login"],
        "Created At": comment["created_at"],
        "Body": comment["body"]
    } for comment in comments[midpoint:]]
 
    return {"Old Comments": old_comments, "New Comments": new_comments}
 
 
def fetch_all_open_prs(repo_owner, repo_name):
    """Fetches details of all open PRs along with file changes, diffs, and comments."""
    all_prs = []
    page = 1
    per_page = 100  # Max allowed by GitHub API
 
    check_rate_limit()  # Check API rate limit before starting
 
    while True:
        url = f"{BASE_URL}/repos/{repo_owner}/{repo_name}/pulls?state=open&per_page={per_page}&page={page}"
        response = requests.get(url, headers=HEADERS)
 
        if response.status_code != 200:
            print(f"Error fetching open PRs: {response.json()}")
            break
 
        data = response.json()
        if not data:
            break  # No more PRs to fetch
 
        for pr in data:
            pr_number = pr["number"]
            print(f"🔍 Processing Open PR #{pr_number}")
 
            file_changes = fetch_file_changes(pr_number, repo_owner, repo_name)
            comments = fetch_pr_comments(pr_number, repo_owner, repo_name)
 
            pr_info = {
                "PR Number": pr_number,
                "Title": pr["title"],
                "State": pr["state"],
                "Author": pr["user"]["login"],
                "Created Date": pr["created_at"],
                "Base Branch": pr["base"]["ref"],
                "Head Branch": pr["head"]["ref"],
                "Merge Conflict": not pr.get("mergeable", True),
                "File Changes": file_changes,
                "Old Comments": comments["Old Comments"],
                "New Comments": comments["New Comments"]
            }
 
            all_prs.append(pr_info)
 
        print(f"Fetched {len(data)} PRs from page {page}")
        page += 1  # Go to next page
 
    if not all_prs:
        print("No open PRs found.")
        return
 
    os.makedirs("data/raw/open_pr", exist_ok=True)
    file_path = f"data/raw/open_pr/{repo_name}_all_open_prs.json"
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(all_prs, file, indent=4)
 
    print(f"Fetched all open PRs")
    print(f"PR details saved in {file_path}")
   
if __name__ == "__main__":
    repo_owner = "pypa"
    repo_name = "wheel"
   
    # Fetch closed PRs
    fetch_all_open_prs(repo_owner, repo_name)