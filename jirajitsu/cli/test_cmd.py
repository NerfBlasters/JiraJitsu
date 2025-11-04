"""
Test command for JiraJitsu - test single issue migration
"""
import click
from rich.console import Console
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu.process_data import ProcessData
from jirajitsu.jira_api import JiraApi
from jirajitsu.log_handler import LogHandler

console = Console()


@click.command()
@click.option('--issue', required=True, help='Issue key to test (e.g., RFM-123)')
@click.option('--verbose', is_flag=True, help='Show detailed output')
@click.pass_context
def test(ctx, issue, verbose):
    """
    Test migration of a single issue

    Migrate one issue to verify configuration and process.

    Example:
        jirajitsu test --issue RFM-123
    """

    log_level = 'DEBUG' if verbose else ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print(f"[bold blue]Testing Migration of Issue: {issue}[/bold blue]\n")

    try:
        jira_api = JiraApi()
        process_data = ProcessData()

        # Verify issue exists
        console.print(f"[cyan]Fetching issue information...[/cyan]")
        success, issue_info = jira_api.get_issue_info(issue)

        if not success:
            console.print(f"[red]✗ Issue {issue} not found or inaccessible[/red]")
            sys.exit(1)

        console.print(f"[green]✓ Issue found[/green]")
        console.print(f"  Summary: {issue_info['fields']['summary']}")
        console.print(f"  Status: {issue_info['fields']['status']['name']}")
        console.print(f"  Assignee: {issue_info['fields']['assignee']['displayName'] if issue_info['fields']['assignee'] else 'Unassigned'}")
        console.print()

        # Check for attachments
        attachments = issue_info['fields']['attachment']
        if attachments:
            console.print(f"[cyan]Issue has {len(attachments)} attachment(s)[/cyan]")

        # Check for comments
        comments = issue_info['fields']['comment']['comments']
        if comments:
            console.print(f"[cyan]Issue has {len(comments)} comment(s)[/cyan]")

        console.print()

        # Confirm migration
        if not click.confirm(f'Proceed with test migration of {issue}?', default=True):
            console.print("[yellow]Test cancelled[/yellow]")
            return

        # Download attachments if any
        if attachments:
            console.print("[cyan]Downloading attachments...[/cyan]")
            jira_api.get_attachment(issue, issue_info)
            console.print("[green]✓ Attachments downloaded[/green]\n")

        # Perform migration
        console.print(f"[bold green]Migrating {issue} to JitBit...[/bold green]\n")
        process_data._migrate_to_jitbit(issue, issue_info)

        console.print(f"\n[bold green]✓ Test migration of {issue} complete![/bold green]")
        console.print("[yellow]Check JitBit to verify the migrated ticket[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Error during test migration: {str(e)}[/red]")
        raise
