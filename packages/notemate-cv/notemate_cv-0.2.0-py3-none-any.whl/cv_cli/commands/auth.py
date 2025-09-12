# File: cv_cli/commands/auth.py

import click
import requests
from getpass import getpass
from cv_cli.utils import save_token, API_BASE_URL

@click.command()
def login():
    """Log in to your NoteMate account."""
    username = click.prompt("Enter your NoteMate username")
    password = getpass("Enter your password: ")
    try:
        # Note: Production login should be more secure, this is for our CLI API
        response = requests.post(f"{API_BASE_URL}/api/cli/login", json={"username": username, "password": password})
        if response.status_code == 200 and response.json().get('success'):
            save_token(response.json().get("token"))
        else:
            error_msg = response.json().get('error', 'Unknown error')
            click.secho(f"❌ Login failed: {error_msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"❌ Connection error: {e}", fg="red")