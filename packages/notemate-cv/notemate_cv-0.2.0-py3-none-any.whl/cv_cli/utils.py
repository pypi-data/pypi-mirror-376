# File: cv_cli/utils.py (Updated)

import os
import json
import requests
from getpass import getpass
import click

# --- Configuration ---
# ▼▼▼ SIRF YEH LINE CHANGE KARNI HAI ▼▼▼
API_BASE_URL = "http://192.168.29.67:5000" 
# ▲▲▲ 5000 ko 5001 kar diya ▲▲▲

CREDENTIALS_FILE = os.path.expanduser("~/.notemate_credentials")

# --- Helper Functions ---

def save_token(token):
    """API token ko user ki home directory mein save karta hai."""
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump({"token": token}, f)
    os.chmod(CREDENTIALS_FILE, 0o600)
    click.secho("✅ You are now logged in.", fg="green")

def load_token():
    """Saved API token ko load karta hai."""
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as f:
        try:
            return json.load(f).get("token")
        except json.JSONDecodeError:
            return None

def get_authenticated_session():
    """Ek authenticated requests.Session object banata hai."""
    token = load_token()
    if not token:
        click.secho("❌ You are not logged in. Please run 'cv login' first.", fg="red")
        return None
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session

def find_repo_root():
    """Current directory se upar jaakar .cv folder dhoondta hai."""
    current_dir = os.getcwd()
    while current_dir != os.path.dirname(current_dir):
        if ".cv" in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    return None

def get_current_branch(root):
    """Gets the name of the current branch from HEAD."""
    head_file = os.path.join(root, ".cv", "HEAD")
    if not os.path.exists(head_file):
        return None
    with open(head_file, "r") as f:
        content = f.read().strip()
        if content.startswith("ref: "):
            return content.split('/')[-1]
    return None

def get_branch_head_commit(root, branch_name):
    """Gets the commit hash a branch is pointing to."""
    branch_file = os.path.join(root, ".cv", "refs", "heads", branch_name)
    if not os.path.exists(branch_file):
        return None
    with open(branch_file, "r") as f:
        return f.read().strip()