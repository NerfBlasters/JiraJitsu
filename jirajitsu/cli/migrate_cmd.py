"""
Migration command for JiraJitsu
"""
import click
from rich.console import Console
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu.process_data import ProcessData
from jirajitsu.log_handler import LogHandler
from jirajitsu.jira_api import JiraApi
from jirajitsu import config

console = Console()


@click.command()
@click.option('--filter-id', type=int, help='Override JIRA filter ID from config')
@click.option('--jql', type=str, help='Use custom JQL query instead of filter')
@click.option('--project', type=str, help='Migrate specific project')
@click.option('--range', 'issue_range', type=str, help='Issue range (e.g., 100:200) - requires --project')
@click.option('--issues', type=str, help='Comma-separated list of issue keys (e.g., RFM-1,RFM-2)')
@click.option('--category-id', type=int, help='Override JitBit destination category ID')
@click.option('--ignore-missing-users', is_flag=True, help='Do not create missing JitBit users (use JITBIT_DEFAULT_ASSIGN_EMAIL instead)')
@click.option('--dry-run', is_flag=True, help='Show what would be migrated without migrating')
@click.option('--limit', type=int, default=20, help='Number of issues to display in dry-run (0 for all, default: 20)')
@click.pass_context
def migrate(ctx, filter_id, jql, project, issue_range, issues, category_id, ignore_missing_users, dry_run, limit):
    """
    Migrate issues from JIRA to JitBit

    By default, uses the filter ID from config.yml and automatically creates missing JitBit
    users. Missing users will be assigned to JITBIT_DEFAULT_ASSIGN_EMAIL if --ignore-missing-users
    is specified.

    Examples:

        # Use default filter from config (creates missing users)
        jirajitsu migrate

        # Ignore missing users (use default assignee instead)
        jirajitsu migrate --ignore-missing-users

        # Use specific filter
        jirajitsu migrate --filter-id 10000

        # Use custom JQL
        jirajitsu migrate --jql "project = RFM AND status = Done"

        # Migrate project range
        jirajitsu migrate --project RFM --range 100:200

        # Migrate specific issues
        jirajitsu migrate --issues RFM-1,RFM-2,RFM-3

        # Preview without migrating
        jirajitsu migrate --dry-run
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    if dry_run:
        console.print("[bold yellow]DRY RUN MODE - No actual migration will occur[/bold yellow]\n")

    try:
        # Validate mutually exclusive options
        option_count = sum([bool(filter_id), bool(jql), bool(project), bool(issues)])
        if option_count > 1:
            console.print("[red]Error: Only one of --filter-id, --jql, --project, or --issues can be specified[/red]")
            sys.exit(1)

        if issue_range and not project:
            console.print("[red]Error: --range requires --project[/red]")
            sys.exit(1)

        # Initialize APIs
        jira_api = JiraApi()
        # By default, create missing users. Only disable if --ignore-missing-users is set
        create_missing_users = not ignore_missing_users
        process_data = ProcessData(create_missing_users=create_missing_users)

        # Override category if specified
        if category_id:
            console.print(f"[cyan]Using category ID: {category_id}[/cyan]")
            # This would need to be passed to the migration logic
            # For now, we'll note it's requested
            console.print("[yellow]Note: Category override requires code modification to fully implement[/yellow]")

        # Show create missing users status
        if ignore_missing_users:
            console.print("[yellow]Auto-create missing users: DISABLED[/yellow]")
            console.print(f"[yellow]Missing users will be assigned to: {config.JITBIT_DEFAULT_ASSIGN_EMAIL}[/yellow]")
        else:
            console.print("[cyan]Auto-create missing users: ENABLED[/cyan]")

        # Determine which issues to migrate
        if issues:
            # Specific issue list
            issue_keys = [k.strip() for k in issues.split(',')]
            console.print(f"[cyan]Migrating {len(issue_keys)} specified issues[/cyan]\n")

            issues_list = {'issues': [{'key': k} for k in issue_keys]}

        elif jql:
            # Custom JQL
            console.print(f"[cyan]Using JQL query: {jql}[/cyan]\n")
            issues_list = jira_api.get_issues_by_jql(jql)

        elif project:
            # Project-based query
            if issue_range:
                start, end = map(int, issue_range.split(':'))
                console.print(f"[cyan]Migrating {project} issues {start} to {end}[/cyan]\n")
                issues_list = jira_api.get_issues_by_project(project, start, end)
            else:
                console.print(f"[cyan]Migrating all issues from project: {project}[/cyan]\n")
                issues_list = jira_api.get_issues_by_project(project)

        elif filter_id:
            # Specific filter
            console.print(f"[cyan]Using filter ID: {filter_id}[/cyan]\n")
            filter_url = jira_api.get_filter_for_id(filter_id)
            issues_list = jira_api.get_filter(filter_url)

        else:
            # Default filter from config
            console.print(f"[cyan]Using default filter from config: {config.JIRA_FILTER_ID}[/cyan]\n")
            filter_url = jira_api.get_filter_for_id(config.JIRA_FILTER_ID)
            issues_list = jira_api.get_filter(filter_url)

        # Check if any issues found
        issue_list = issues_list.get('issues', [])
        if not issue_list:
            console.print("[yellow]No issues found matching criteria[/yellow]")
            return

        console.print(f"[green]Found {len(issue_list)} issues to migrate[/green]\n")

        if dry_run:
            # Show preview
            console.print("[bold]Preview of issues that would be migrated:[/bold]\n")
            display_limit = len(issue_list) if limit == 0 else min(limit, len(issue_list))
            for i, issue in enumerate(issue_list[:display_limit], 1):
                console.print(f"  {i}. {issue['key']}")

            if limit > 0 and len(issue_list) > limit:
                console.print(f"  [dim]... and {len(issue_list) - limit} more (use --limit 0 to show all)[/dim]")

            console.print(f"\n[bold yellow]DRY RUN COMPLETE - No migration performed[/bold yellow]")
            console.print(f"[yellow]Remove --dry-run flag to perform actual migration[/yellow]")
            return

        # Confirm migration
        if not ctx.obj.get('QUIET'):
            console.print(f"[bold yellow]About to migrate {len(issue_list)} issues from JIRA to JitBit[/bold yellow]")
            if not click.confirm('Continue with migration?', default=True):
                console.print("[yellow]Migration cancelled[/yellow]")
                return

        # Perform migration
        console.print("\n[bold green]Starting migration...[/bold green]\n")

        # Note: category_id override is not yet implemented
        if option_count > 0 or category_id:
            console.print("[yellow]Note: Some CLI options (category override) require additional implementation[/yellow]\n")

        # Pass the prepared issues_list to start()
        process_data.start(issues_list=issues_list)

        console.print("\n[bold green]✓ Migration complete![/bold green]")

    except Exception as e:
        console.print(f"[red]Error during migration: {str(e)}[/red]")
        raise
