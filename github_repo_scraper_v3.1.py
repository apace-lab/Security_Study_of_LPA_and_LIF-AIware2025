import requests
import pandas as pd
import os
import time

# GitHub API settings
GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = "xxx"

# Headers with authentication
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# Topics to search (your provided topics)
topics = [
    "llm", "llms", "openai", "chatgpt", "gpt", "gemini", "llama", "claude", "gen-ai",
    "deepseek", "chatgpt-app", "Gemma", "Mixtral", "chatgpt-desktop", "grok", "falcon"
]

# List of common LLMs to detect in repositories
known_llms = [
    "GPT-4", "GPT-3.5", "GPT-3", "ChatGPT", "Claude", "Claude 2", "Claude 3", "Llama 2",
    "Llama 3", "Gemini", "Mixtral", "DeepSeek", "Falcon", "Mistral", "Vicuna",
    "Dolly", "Command R+", "Command R", "Zephyr", "Phi", "StableLM"
]

# CSV file where results are stored
csv_filepath = "repo_study_summary_revision(popular repos).csv"

# Load existing data if file exists
if os.path.exists(csv_filepath):
    df_existing = pd.read_csv(csv_filepath)
    existing_repos = set(df_existing["GitHub Repository Name"].dropna().tolist())  # Convert to set for fast lookup
else:
    df_existing = pd.DataFrame(columns=[
        "GitHub Repository Name", "Link", "Description", "Major Language", "#Stars", "#Forks", "Used LLMs",
        "Use API Key", "Can Use Shared API Key", "Can Upload Personal Files", "Use Cache", "Use Log"
    ])
    existing_repos = set()  # Empty set if no file exists

# Function to search GitHub repositories by topic
def search_github_by_topic(topic):
    params = {
        "q": f"topic:{topic} stars:>1000",
        "sort": "stars",
        "order": "desc",
        "per_page": 50  # Adjust as needed
    }

    response = requests.get(GITHUB_API_URL, headers=HEADERS, params=params)
    
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Error fetching data for topic {topic}: {response.status_code}")
        return []

# Function to check README for specific keywords (LLMs, API keys, caching, logging)
def analyze_readme(owner, repo):
    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
    
    response = requests.get(readme_url, headers=HEADERS)
    
    if response.status_code != 200:
        # Try checking in "master" branch instead of "main"
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
        response = requests.get(readme_url, headers=HEADERS)
    
    if response.status_code == 200:
        content = response.text.lower()  # Convert to lowercase for better matching

        # Detect LLMs used in the project
        detected_llms = [llm for llm in known_llms if llm.lower() in content]

        if len(detected_llms) > 3:  # If multiple LLMs are detected
            llm_used = "Many major LLMs"
        elif detected_llms:
            llm_used = ", ".join(detected_llms)
        else:
            llm_used = "?"

        # Detect other project features
        api_key = "yes" if any(word in content for word in ["api key required", "requires api key", "set your api key"]) else "?"
        shared_api = "yes" if "shared api key" in content else "?"
        upload_files = "yes" if any(word in content for word in ["upload personal files", "support file uploads"]) else "?"
        cache_usage = "yes" if "cache" in content else "?"
        logging_usage = "yes" if "log" in content else "?"
        
        return llm_used, api_key, shared_api, upload_files, cache_usage, logging_usage

    return "?", "?", "?", "?", "?", "?"  # If README is unavailable, mark unknown

# Collect data
repo_data = []

for topic in topics:
    print(f"🔍 Searching GitHub topic: {topic}...")
    repos = search_github_by_topic(topic)
    
    for repo in repos:
        repo_name = repo["name"]
        
        if repo_name not in existing_repos:  # Avoid duplicates
            existing_repos.add(repo_name)  # Track it

            # Get README analysis
            owner = repo["owner"]["login"]
            repo_id = repo["id"]
            llm_used, api_key, shared_api, upload_files, cache_usage, logging_usage = analyze_readme(owner, repo_name)

            repo_data.append({
                "GitHub Repository Name": repo_name,
                "Link": repo["html_url"],
                "Description": repo["description"] if repo["description"] else "No description available",
                "Major Language": repo["language"] if repo["language"] else "Unknown",
                "#Stars": repo["stargazers_count"],
                "#Forks": repo["forks_count"],
                "Used LLMs": llm_used,  # Now auto-detects LLMs
                "Use API Key": api_key,
                "Can Use Shared API Key": shared_api,
                "Can Upload Personal Files": upload_files,
                "Use Cache": cache_usage,
                "Use Log": logging_usage
            })
    
    # Avoid hitting GitHub API rate limits
    time.sleep(5)  # Pause between requests

# Convert new data to DataFrame
df_new = pd.DataFrame(repo_data)

# Merge new data with existing CSV
df_combined = pd.concat([df_existing, df_new], ignore_index=True)

# Save back to the same CSV file
df_combined.to_csv(csv_filepath, index=False)

print(f"✅ Data collection complete! {len(df_new)} new repositories added with LLM detection. The updated dataset is saved in {csv_filepath}.")
