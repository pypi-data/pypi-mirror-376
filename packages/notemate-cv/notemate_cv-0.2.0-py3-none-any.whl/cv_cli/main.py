# File: cv_cli/main.py (The Final Version)

import click
from cv_cli.commands.vcs import (
    add, 
    commit, 
    branch_command, 
    checkout_command,
    log,
    status,
    push
)
from cv_cli.commands.auth import login
from cv_cli.commands.repo import create, clone, pull

@click.group()
def cli():
    """NoteMate Code Verse (CV) Command Line Interface."""
    pass

# Add all commands to the main group
cli.add_command(login)
cli.add_command(create)
cli.add_command(clone)
cli.add_command(pull)
cli.add_command(add)
cli.add_command(commit)
cli.add_command(branch_command, name='branch')
cli.add_command(checkout_command, name='checkout')
cli.add_command(log)
cli.add_command(status)
cli.add_command(push)