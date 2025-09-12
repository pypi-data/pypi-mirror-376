#!/usr/bin/env python3
"""
CLI for AI-powered GitHub PR code reviews.
"""

import os
import sys
import textwrap
import getpass
import requests
from typing import Optional

try:
    from github import Github
    from github.GithubException import GithubException
except ImportError:
    print("ERROR: PyGithub not installed. Install with: pip install PyGithub")
    sys.exit(1)

# ---------- Configuration ----------
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "mistralai/mistral-7b-instruct"
MAX_DIFF_CHARS = 120_000
# -----------------------------------

# ------------------ Helpers ------------------

def get_credentials(repo_arg: Optional[str] = None):
    """Get GitHub token, OpenRouter API key, and repo (from env, arg, or prompt)."""
    github_token = os.getenv("GITHUB_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if not github_token:
        github_token = getpass.getpass(prompt="Enter your GitHub Personal Access Token: ")

    if not openrouter_key:
        openrouter_key = getpass.getpass(prompt="Enter your OpenRouter API Key: ")

    if repo_arg:
        repo_full_name = repo_arg
    else:
        repo_full_name = input("Enter target repository (format: owner/repo): ").strip()

    if not repo_full_name or "/" not in repo_full_name:
        print("ERROR: Repository name must be in format 'owner/repo'. Exiting.")
        sys.exit(1)

    return github_token, openrouter_key, repo_full_name


def connect_github(github_token: str) -> Github:
    print("Connecting to GitHub...")
    try:
        gh = Github(github_token, per_page=100)
        user = gh.get_user().login
        print(f"Authenticated as GitHub user: {user}")
        return gh
    except GithubException as e:
        print("Failed to authenticate with GitHub. Check your token.")
        raise e
    except Exception as e:
        print("Unexpected error connecting to GitHub:", e)
        raise e


def fetch_open_prs(gh: Github, repo_full_name: str):
    print(f"Looking up repository '{repo_full_name}'...")
    try:
        repo = gh.get_repo(repo_full_name)
    except GithubException as e:
        print(f"Repository '{repo_full_name}' not found or access denied.")
        raise e

    print("Fetching open pull requests...")
    open_prs = list(repo.get_pulls(state="open", sort="created", direction="asc"))
    print(f"Found {len(open_prs)} open PR(s).")
    return open_prs


def get_pr_diff(pr, github_token: str) -> Optional[str]:
    print(f"  - Fetching diff for PR #{pr.number}: {pr.title!r} ...")
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "auto-code-review-script"
    }
    try:
        resp = requests.get(pr.diff_url, headers=headers, timeout=30)
        resp.raise_for_status()
        diff_text = resp.text
        if len(diff_text) > MAX_DIFF_CHARS:
            print(f"    WARNING: diff too long, trimming to last {MAX_DIFF_CHARS} chars.")
            diff_text = "[TRIMMED]\n" + diff_text[-MAX_DIFF_CHARS:]
        return diff_text
    except Exception as e:
        print(f"    ERROR fetching diff for PR #{pr.number}: {e}")
        return None


def build_system_prompt(pr, diff_text: str) -> str:
    header = textwrap.dedent(f"""
    You are a senior software engineer and code reviewer.
    Review this PR: #{pr.number} - {pr.title}
    Author: {pr.user.login if pr.user else 'unknown'}
    URL: {pr.html_url}

    Focus on correctness, security, readability, performance, maintainability, tests.
    Provide actionable suggestions, code snippets if needed, and a checklist of next steps.
    """).strip()
    return f"{header}\n\n--- RAW DIFF START ---\n{diff_text}\n--- RAW DIFF END ---\nPlease produce the review."


def get_ai_review(openrouter_key: str, system_prompt: str, model: str = DEFAULT_MODEL, max_tokens: int = 1000) -> Optional[str]:
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "Content-Type": "application/json",
        "User-Agent": "auto-code-review-script"
    }
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "top_p": 1.0,
        "n": 1
    }
    try:
        resp = requests.post(OPENROUTER_ENDPOINT, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # Extract generated text
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception:
            try:
                return data["choices"][0]["text"].strip()
            except Exception:
                print("Could not parse AI review from response.")
                return None
    except Exception as e:
        print(f"Error calling OpenRouter API: {e}")
        return None


def post_review_to_pr(pr, review_text: str):
    print(f"    - Posting review to PR #{pr.number}...")
    try:
        pr.create_review(body=review_text, event="COMMENT")
        print(f"    - Posted review to PR #{pr.number}.")
    except Exception as e:
        print(f"    ERROR posting review: {e}")


# ------------------ Main CLI ------------------

def main(repo_arg: Optional[str] = None):
    github_token, openrouter_key, repo_full_name = get_credentials(repo_arg)
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    print(f"Using OpenRouter model: {model}")

    gh = connect_github(github_token)
    open_prs = fetch_open_prs(gh, repo_full_name)
    if not open_prs:
        print("No open PRs. Exiting.")
        return

    for pr in open_prs:
        print(f"\nProcessing PR #{pr.number}: {pr.title}")
        diff = get_pr_diff(pr, github_token)
        if not diff:
            print(f"  Skipping PR #{pr.number} due to diff error.")
            continue
        prompt = build_system_prompt(pr, diff)
        ai_review = get_ai_review(openrouter_key, prompt, model=model)
        if not ai_review:
            print(f"  Skipping PR #{pr.number} because AI review could not be obtained.")
            continue
        post_review_to_pr(pr, ai_review)

    print("\nAll done. Processed all open PRs.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI-powered GitHub PR code review CLI")
    parser.add_argument("--repo", help="Target repository (owner/repo)")
    args = parser.parse_args()
    main(args.repo)
