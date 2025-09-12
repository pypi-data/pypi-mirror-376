# File: cv_cli/commands/vcs.py (Fully Updated and Finalized)

import os
import json
import click
import hashlib
import time
from datetime import datetime
import requests # <-- ### 🟢 YEH HAI ASLI FIX 🟢 ###
from cv_cli.utils import (
    find_repo_root, 
    get_current_branch, 
    get_branch_head_commit,
    get_authenticated_session,
    API_BASE_URL
)

@click.command()
@click.argument('filenames', nargs=-1, required=True)
def add(filenames):
    """Add file contents to the staging area (the index)."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red")
        return

    index_file = os.path.join(root, ".cv", "index")
    objects_dir = os.path.join(root, ".cv", "objects")
    os.makedirs(objects_dir, exist_ok=True)
    
    try:
        with open(index_file, "r") as f: index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        index = {}

    files_to_add = filenames
    if filenames == ('.',):
        files_to_add = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f)) and ".cv" not in f]

    for fname in files_to_add:
        filepath = os.path.join(root, fname)
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
                sha1_hash = hashlib.sha1(content).hexdigest()
            
            with open(os.path.join(objects_dir, sha1_hash), "wb") as f:
                f.write(content)
            
            index[fname] = sha1_hash
            click.echo(f"Added '{fname}' to index.")
        else:
            click.secho(f"Warning: File '{fname}' not found.", fg="yellow")

    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)

@click.command()
@click.option('-m', '--message', required=True, help='Commit message.')
def commit(message):
    """Record changes to the repository locally."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red")
        return

    index_file = os.path.join(root, ".cv", "index")
    try:
        with open(index_file, "r") as f: index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): index = {}

    if not index:
        click.secho("🤷‍♂️ Nothing to commit. Use 'cv add <file>' to stage changes.", fg="yellow"); return
    
    current_branch = get_current_branch(root)
    
    if not current_branch:
        current_branch = 'main'
        click.echo(f"No current branch found. This will be the first commit on 'main'.")
        os.makedirs(os.path.join(root, ".cv", "refs", "heads"), exist_ok=True)
        with open(os.path.join(root, ".cv", "HEAD"), "w") as f:
            f.write(f"ref: refs/heads/{current_branch}")

    parent_commit = get_branch_head_commit(root, current_branch)

    commit_data = {
        "parent": parent_commit,
        "message": message,
        "timestamp": time.time(),
        "files": index
    }
    
    commit_content = json.dumps(commit_data, sort_keys=True).encode('utf-8')
    commit_hash = hashlib.sha1(commit_content).hexdigest()
    
    objects_dir = os.path.join(root, ".cv", "objects")
    with open(os.path.join(objects_dir, commit_hash), "w") as f:
        json.dump(commit_data, f, indent=2)

    branch_file = os.path.join(root, ".cv", "refs", "heads", current_branch)
    with open(branch_file, "w") as f:
        f.write(commit_hash)
        
    open(index_file, "w").close()
    click.secho(f"✅ [{current_branch}] Changes committed locally: {commit_hash[:7]}", fg="green")

@click.command(name="branch")
@click.argument('branch_name', required=False)
def branch_command(branch_name):
    """List branches or create a new one."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red"); return

    heads_dir = os.path.join(root, ".cv", "refs", "heads")
    os.makedirs(heads_dir, exist_ok=True)
    current_branch = get_current_branch(root)

    if not branch_name:
        if not current_branch:
             click.echo("No branches yet. Make your first commit to create the 'main' branch.")
             return
        branches = os.listdir(heads_dir)
        for b in branches:
            if b == current_branch:
                click.secho(f"* {b}", fg="green")
            else:
                click.echo(f"  {b}")
        return

    new_branch_file = os.path.join(heads_dir, branch_name)
    if os.path.exists(new_branch_file):
        click.secho(f"❌ Branch '{branch_name}' already exists.", fg="red"); return

    current_commit = get_branch_head_commit(root, current_branch)
    if not current_commit:
         click.secho(f"❌ Cannot create branch. No commits found in '{current_branch}'.", fg="red"); return

    with open(new_branch_file, "w") as f:
        f.write(current_commit)
    click.secho(f"✅ New branch '{branch_name}' created.", fg="green")

@click.command(name="checkout")
@click.argument('branch_name')
def checkout_command(branch_name):
    """Switch branches and update working directory."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red"); return

    commit_hash = get_branch_head_commit(root, branch_name)
    if not commit_hash:
        click.secho(f"❌ Branch '{branch_name}' not found.", fg="red"); return
    
    objects_dir = os.path.join(root, ".cv", "objects")
    with open(os.path.join(objects_dir, commit_hash), "r") as f:
        commit_data = json.load(f)
    
    for entry in os.listdir(root):
        if os.path.isfile(os.path.join(root, entry)) and ".cv" not in entry:
            os.remove(os.path.join(root, entry))
    
    for filename, file_hash in commit_data['files'].items():
        with open(os.path.join(objects_dir, file_hash), "rb") as blob_f:
            with open(os.path.join(root, filename), "wb") as target_f:
                target_f.write(blob_f.read())
    
    with open(os.path.join(root, ".cv", "HEAD"), "w") as f:
        f.write(f"ref: refs/heads/{branch_name}")
        
    click.secho(f"✅ Switched to branch '{branch_name}'.", fg="green")

@click.command()
def log():
    """Show the commit history for the current branch."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red"); return

    current_branch = get_current_branch(root)
    if not current_branch:
        click.echo("No commits yet. Make your first commit."); return

    commit_hash = get_branch_head_commit(root, current_branch)
    if not commit_hash:
        click.echo(f"No commits in branch '{current_branch}' yet."); return

    click.secho(f"History for branch '{current_branch}':\n", bold=True)
    
    while commit_hash:
        objects_dir = os.path.join(root, ".cv", "objects")
        commit_file = os.path.join(objects_dir, commit_hash)
        if not os.path.exists(commit_file):
            click.secho(f"❌ Error: Missing commit object {commit_hash}", fg="red"); break
        with open(commit_file, "r") as f:
            commit_data = json.load(f)
        click.secho(f"commit {commit_hash}", fg="yellow")
        ts = datetime.fromtimestamp(commit_data['timestamp']).strftime('%a %b %d %H:%M:%S %Y')
        click.echo(f"Date:   {ts}")
        click.echo(f"\n\t{commit_data['message']}\n")
        commit_hash = commit_data.get('parent')

@click.command()
def status():
    """Show the working tree status."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red"); return

    current_branch = get_current_branch(root)
    if not current_branch:
        click.echo("On a new repository. Make your first commit to create the 'main' branch."); return

    click.secho(f"On branch {current_branch}", bold=True)
    
    index_file = os.path.join(root, ".cv", "index")
    try:
        with open(index_file, "r") as f: staged_files = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        staged_files = {}

    if staged_files:
        click.secho("\nChanges to be committed:", fg="green")
        for filename in staged_files:
            click.echo(f"\tnew file:   {filename}")
    
    all_local_files = {f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))}
    last_commit_hash = get_branch_head_commit(root, get_current_branch(root))
    tracked_files = set()
    if last_commit_hash:
        with open(os.path.join(root, ".cv", "objects", last_commit_hash)) as f:
            last_commit_data = json.load(f)
            tracked_files = set(last_commit_data['files'].keys())

    untracked_files = all_local_files - tracked_files - set(staged_files.keys())
    
    if untracked_files:
        click.secho("\nUntracked files:", fg="red")
        for filename in untracked_files:
            click.echo(f"\t{filename}")

    if not staged_files and not untracked_files:
        click.echo("\nNothing to commit, working tree clean.")

@click.command()
def push():
    """Push local commits to the remote repository."""
    root = find_repo_root()
    if not root:
        click.secho("❌ Not a Code Verse repository.", fg="red"); return
        
    session = get_authenticated_session()
    if not session: return

    with open(os.path.join(root, ".cv", "config"), "r") as f:
        repo_id = json.load(f).get("repo_id")
    
    current_branch = get_current_branch(root)
    local_head_commit = get_branch_head_commit(root, current_branch)

    try:
        res = session.get(f"{API_BASE_URL}/api/cli/repo/{repo_id}/branch_head/{current_branch}")
        res.raise_for_status()
        remote_head_commit = res.json().get('commit_hash')

        if local_head_commit == remote_head_commit:
            click.secho("✅ Everything is up-to-date.", fg="green")
            return

        commits_to_push = {}
        commit_hash_to_trace = local_head_commit
        objects_dir = os.path.join(root, ".cv", "objects")
        
        while commit_hash_to_trace and commit_hash_to_trace != remote_head_commit:
            with open(os.path.join(objects_dir, commit_hash_to_trace), "r") as f:
                commit_data = json.load(f)
            commits_to_push[commit_hash_to_trace] = commit_data
            commit_hash_to_trace = commit_data.get('parent')

        if not commits_to_push:
            click.secho("🤷‍♂️ No new local commits to push.", fg="yellow")
            return

        commits_to_push = dict(reversed(list(commits_to_push.items())))
        click.echo(f"Uploading {len(commits_to_push)} commit(s) to branch '{current_branch}'...")

        push_res = session.post(
            f"{API_BASE_URL}/api/cli/repo/{repo_id}/push",
            json={
                "branch": current_branch,
                "commits": commits_to_push
            }
        )
        push_res.raise_for_status()
        
        click.secho(f"✅ {push_res.json().get('message')}", fg="green")

    except requests.exceptions.HTTPError as e:
        error_detail = "Unknown server error."
        try:
            error_detail = e.response.json().get('message', e.response.text)
        except json.JSONDecodeError:
            error_detail = e.response.text
        click.secho(f"❌ Push failed (HTTP {e.response.status_code}): {error_detail}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Connection Error: {e}", fg="red")
    except Exception as e:
        click.secho(f"❌ An unexpected error occurred: {e}", fg="red")