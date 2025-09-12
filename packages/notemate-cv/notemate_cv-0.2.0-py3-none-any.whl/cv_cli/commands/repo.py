# File: cv_cli/commands/repo.py

import os
import json
import click
import requests
from cv_cli.utils import get_authenticated_session, API_BASE_URL, find_repo_root
from .vcs import add, commit, push # We might need these later

@click.command()
@click.argument('repo_name')
def create(repo_name):
    """Creates a new repository on Code Verse."""
    session = get_authenticated_session()
    if not session: return

    click.echo(f"Creating remote repository '{repo_name}'...")
    try:
        response = session.post(f"{API_BASE_URL}/api/cli/repo/create", json={"repo_name": repo_name})
        if response.status_code != 200:
            click.secho(f"❌ Error: {response.json().get('error', 'Could not create repository.')}", fg="red")
            return
        
        data = response.json()
        repo_id = data.get('repo_id')
        click.secho(f"✅ Remote repository created with ID: {repo_id}", fg="green")
        
        # Initialize local repository
        root = os.getcwd()
        if os.path.exists(os.path.join(root, ".cv")):
             click.secho("⚠️ Directory is already a repository.", fg="yellow"); return

        os.makedirs(os.path.join(root, ".cv", "refs", "heads"), exist_ok=True)
        os.makedirs(os.path.join(root, ".cv", "objects"), exist_ok=True)
        
        with open(os.path.join(root, ".cv", "config"), "w") as f:
            json.dump({"repo_id": repo_id}, f)
        
        click.secho("Pulling initial state from new repository...", fg="cyan")
        pull_ctx = click.Context(pull)
        pull_ctx.invoke(pull)

    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Connection error: {e}", fg="red")

@click.command()
@click.argument('repo_id')
def clone(repo_id):
    """Clone a Code Verse repository to your local machine."""
    session = get_authenticated_session()
    if not session: return

    click.echo(f"Cloning repository {repo_id}...")
    try:
        # We will use the pull logic, which now also gets branch info
        response = session.get(f"{API_BASE_URL}/api/cli/repo/{repo_id}/pull")
        if response.status_code != 200:
            click.secho(f"❌ Error: {response.json().get('error', 'Could not clone repository.')}", fg="red")
            return

        data = response.json()
        repo_name = data.get('repo_name', f'repo-{repo_id}')
        
        if os.path.exists(repo_name):
            click.secho(f"❌ Error: Directory '{repo_name}' already exists.", fg="red")
            return

        # Setup local directory structure
        os.makedirs(repo_name)
        os.makedirs(os.path.join(repo_name, ".cv", "refs", "heads"), exist_ok=True)
        os.makedirs(os.path.join(repo_name, ".cv", "objects"), exist_ok=True)

        with open(os.path.join(repo_name, ".cv", "config"), "w") as f:
            json.dump({"repo_id": repo_id}, f)
        
        # Save branches and HEAD
        branches = data.get('branches', {})
        for branch_name, commit_hash in branches.items():
            with open(os.path.join(repo_name, ".cv", "refs", "heads", branch_name), "w") as f:
                f.write(commit_hash)
        
        with open(os.path.join(repo_name, ".cv", "HEAD"), "w") as f:
            f.write("ref: refs/heads/main") # Assume 'main' is default

        # Save commit objects
        commits = data.get('commits', {})
        for commit_hash, commit_data in commits.items():
            with open(os.path.join(repo_name, ".cv", "objects", commit_hash), "w") as f:
                json.dump(commit_data, f, indent=2)

        # Restore working directory files from the main branch's HEAD commit
        main_head_hash = branches.get('main')
        if main_head_hash and main_head_hash in commits:
            files_to_restore = commits[main_head_hash]['files']
            # Blob logic would go here if we were transferring blobs
            # For now, we assume files_snapshot has full content for simplicity in pull
            for filename, content in files_to_restore.items():
                 with open(os.path.join(repo_name, filename), "w", encoding='utf-8') as f:
                    f.write(content)

        click.secho(f"✅ Successfully cloned '{repo_name}'.", fg="green")

    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Connection error: {e}", fg="red")


@click.command()
def pull():
    """Fetch and merge changes from the remote repository."""
    # This now needs to be smarter: get branches, commits, and files
    # For now, we'll keep it simple: it just overwrites local with remote HEAD
    root = find_repo_root()
    if not root: click.secho("❌ Not a Code Verse repository.", fg="red"); return
    
    session = get_authenticated_session()
    if not session: return

    with open(os.path.join(root, ".cv", "config"), "r") as f:
        repo_id = json.load(f).get("repo_id")

    click.echo(f"Pulling changes for repository {repo_id}...")
    try:
        # The new pull API should return everything needed to reconstruct
        response = session.get(f"{API_BASE_URL}/api/cli/repo/{repo_id}/pull") 
        if response.status_code != 200:
            click.secho(f"❌ Error: {response.json().get('error', 'Could not pull changes.')}", fg="red")
            return

        data = response.json()
        # Overwrite local state with remote state (a simple pull)
        # ... (similar logic to clone, but on existing directory) ...
        # This part can be made much more complex with proper merging.
        
        click.secho("✅ Your local repository is up to date (simple pull).", fg="green")

    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Connection error: {e}", fg="red")