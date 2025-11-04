"""
Validation commands for JiraJitsu
"""
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu.jira_api import JiraApi
from jirajitsu.jitbit_api import JitbitApi
from jirajitsu.log_handler import LogHandler
from jirajitsu import config

console = Console()


@click.group()
@click.pass_context
def validate(ctx):
    """
    Validate configuration and user mappings

    Check that everything is properly configured before migration.
    """
    pass


@validate.command('config')
@click.pass_context
def validate_config(ctx):
    """Validate configuration and test API connections"""

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print("[bold blue]Validating JiraJitsu Configuration[/bold blue]\n")

    all_valid = True

    # Check JIRA connection
    console.print("[cyan]Testing JIRA connection...[/cyan]")
    try:
        jira_api = JiraApi()
        if jira_api.check_url_and_user():
            console.print("✓ [green]JIRA connection successful[/green]")
        else:
            console.print("✗ [red]JIRA connection failed[/red]")
            all_valid = False
    except Exception as e:
        console.print(f"✗ [red]JIRA error: {str(e)}[/red]")
        all_valid = False

    # Check JitBit connection
    console.print("[cyan]Testing JitBit connection...[/cyan]")
    try:
        jitbit_api = JitbitApi()
        if jitbit_api.check_url_and_user():
            console.print("✓ [green]JitBit connection successful[/green]")
        else:
            console.print("✗ [red]JitBit connection failed[/red]")
            all_valid = False
    except Exception as e:
        console.print(f"✗ [red]JitBit error: {str(e)}[/red]")
        all_valid = False

    # Check directories
    console.print("[cyan]Checking directories...[/cyan]")
    try:
        if os.path.isdir(config.ATTACHMENT_FOLDER):
            console.print(f"✓ [green]Attachment folder exists: {config.ATTACHMENT_FOLDER}[/green]")
        else:
            console.print(f"✗ [red]Attachment folder missing: {config.ATTACHMENT_FOLDER}[/red]")
            all_valid = False

        if os.path.isdir(config.LOG_DIR):
            console.print(f"✓ [green]Log directory exists: {config.LOG_DIR}[/green]")
        else:
            console.print(f"✗ [red]Log directory missing: {config.LOG_DIR}[/red]")
            all_valid = False
    except Exception as e:
        console.print(f"✗ [red]Directory check error: {str(e)}[/red]")
        all_valid = False

    # Check category IDs
    console.print("[cyan]Validating category IDs...[/cyan]")
    try:
        categories = jitbit_api.get_categories()
        category_ids = [cat['CategoryID'] for cat in categories]

        if config.JITBIT_MIGRATE_CATEGORY_ID in category_ids:
            console.print(f"✓ [green]Migration category ID valid: {config.JITBIT_MIGRATE_CATEGORY_ID}[/green]")
        else:
            console.print(f"✗ [red]Migration category ID invalid: {config.JITBIT_MIGRATE_CATEGORY_ID}[/red]")
            all_valid = False

        if config.JITBIT_DELETE_CATEGORY_ID:
            if config.JITBIT_DELETE_CATEGORY_ID in category_ids:
                console.print(f"✓ [green]Delete category ID valid: {config.JITBIT_DELETE_CATEGORY_ID}[/green]")
            else:
                console.print(f"✗ [red]Delete category ID invalid: {config.JITBIT_DELETE_CATEGORY_ID}[/red]")
                all_valid = False
    except Exception as e:
        console.print(f"✗ [red]Category validation error: {str(e)}[/red]")
        all_valid = False

    # Check filter ID
    console.print("[cyan]Validating JIRA filter...[/cyan]")
    try:
        filter_url = jira_api.get_filter_for_id(config.JIRA_FILTER_ID)
        if filter_url:
            console.print(f"✓ [green]JIRA filter ID valid: {config.JIRA_FILTER_ID}[/green]")
        else:
            console.print(f"✗ [red]JIRA filter ID invalid: {config.JIRA_FILTER_ID}[/red]")
            all_valid = False
    except Exception as e:
        console.print(f"✗ [red]Filter validation error: {str(e)}[/red]")
        all_valid = False

    # Summary
    console.print()
    if all_valid:
        console.print("[bold green]✓ All validations passed! Configuration is ready.[/bold green]")
        sys.exit(0)
    else:
        console.print("[bold red]✗ Some validations failed. Please fix the issues above.[/bold red]")
        sys.exit(1)


@validate.command('users')
@click.option('--create-missing', is_flag=True, help='Create missing JitBit users')
@click.option('--output', type=click.Path(), help='Save report to CSV file')
@click.pass_context
def validate_users(ctx, create_missing, output):
    """
    Validate that JIRA users exist in JitBit

    Check all JIRA users and verify they exist in JitBit with proper permissions.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print("[bold blue]Validating User Mappings[/bold blue]\n")

    try:
        jira_api = JiraApi()
        jitbit_api = JitbitApi()

        # Fetch users
        console.print("[cyan]Fetching JIRA users...[/cyan]")
        jira_users = jira_api.get_all_users()
        console.print(f"Found {len(jira_users)} JIRA users\n")

        console.print("[cyan]Fetching JitBit users...[/cyan]")
        jitbit_users = jitbit_api.get_users()
        jitbit_emails = {user.get('Email', '').lower() for user in jitbit_users if user.get('Email')}
        console.print(f"Found {len(jitbit_users)} JitBit users\n")

        # Validate mappings
        report = []
        missing_users = []
        non_technician_users = []

        with Progress() as progress:
            task = progress.add_task("[cyan]Validating users...", total=len(jira_users))

            for jira_user in jira_users:
                email = jira_user.get('emailAddress', '').lower()
                display_name = jira_user.get('displayName', 'N/A')

                if not email:
                    report.append({
                        'JIRA User': display_name,
                        'Email': 'N/A',
                        'Status': 'No Email',
                        'JitBit ID': 'N/A',
                        'Technician': 'N/A'
                    })
                    progress.advance(task)
                    continue

                # Check if exists in JitBit
                if email in jitbit_emails:
                    # Get full user details
                    user_id = jitbit_api.get_user_id_by_email(email)
                    is_tech = jitbit_api.get_user_is_technician(user_id) if user_id > 0 else False

                    report.append({
                        'JIRA User': display_name,
                        'Email': email,
                        'Status': 'Exists',
                        'JitBit ID': str(user_id),
                        'Technician': 'Yes' if is_tech else 'No'
                    })

                    if not is_tech:
                        non_technician_users.append((display_name, email))
                else:
                    # Missing in JitBit
                    missing_users.append((display_name, email))

                    if create_missing:
                        # Parse name
                        name_parts = display_name.split()
                        first_name = name_parts[0] if len(name_parts) > 0 else display_name
                        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                        # Create user
                        console.print(f"[yellow]Creating user: {email}[/yellow]")
                        new_id = jitbit_api.create_user(email, first_name, last_name, is_technician=False)

                        report.append({
                            'JIRA User': display_name,
                            'Email': email,
                            'Status': 'Created',
                            'JitBit ID': str(new_id),
                            'Technician': 'No'
                        })
                    else:
                        report.append({
                            'JIRA User': display_name,
                            'Email': email,
                            'Status': 'Missing',
                            'JitBit ID': 'N/A',
                            'Technician': 'N/A'
                        })

                progress.advance(task)

        # Display summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"Total JIRA users: {len(jira_users)}")
        console.print(f"[green]Existing in JitBit: {len(jira_users) - len(missing_users)}[/green]")

        if missing_users and not create_missing:
            console.print(f"[red]Missing in JitBit: {len(missing_users)}[/red]")
            console.print("\n[yellow]Missing users:[/yellow]")
            for name, email in missing_users[:10]:  # Show first 10
                console.print(f"  - {name} ({email})")
            if len(missing_users) > 10:
                console.print(f"  ... and {len(missing_users) - 10} more")

        if non_technician_users:
            console.print(f"\n[yellow]Non-technician users (cannot be assigned): {len(non_technician_users)}[/yellow]")
            for name, email in non_technician_users[:10]:
                console.print(f"  - {name} ({email})")
            if len(non_technician_users) > 10:
                console.print(f"  ... and {len(non_technician_users) - 10} more")

        # Save report if requested
        if output:
            import csv
            with open(output, 'w', newline='') as f:
                if report:
                    writer = csv.DictWriter(f, fieldnames=report[0].keys())
                    writer.writeheader()
                    writer.writerows(report)
            console.print(f"\n[green]Report saved to: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@validate.command('filter')
@click.option('--filter-id', type=int, help='Filter ID to validate (defaults to config)')
@click.option('--jql', type=str, help='JQL query to validate')
@click.option('--project', type=str, help='Project key to validate')
@click.option('--range', 'issue_range', type=str, help='Issue range (e.g., 100:200)')
@click.pass_context
def validate_filter(ctx, filter_id, jql, project, issue_range):
    """
    Preview issues that would be migrated

    Show which issues match the filter/query without actually migrating.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    try:
        jira_api = JiraApi()
        jitbit_api = JitbitApi()

        # Determine which query to use
        if jql:
            console.print(f"[cyan]Testing JQL query: {jql}[/cyan]\n")
            issues_list = jira_api.get_issues_by_jql(jql)
        elif project:
            if issue_range:
                start, end = map(int, issue_range.split(':'))
                console.print(f"[cyan]Testing project {project} range {start}-{end}[/cyan]\n")
                issues_list = jira_api.get_issues_by_project(project, start, end)
            else:
                console.print(f"[cyan]Testing project {project}[/cyan]\n")
                issues_list = jira_api.get_issues_by_project(project)
        elif filter_id:
            console.print(f"[cyan]Testing filter ID: {filter_id}[/cyan]\n")
            filter_url = jira_api.get_filter_for_id(filter_id)
            issues_list = jira_api.get_filter(filter_url)
        else:
            # Use default from config
            console.print(f"[cyan]Testing default filter: {config.JIRA_FILTER_ID}[/cyan]\n")
            filter_url = jira_api.get_filter_for_id(config.JIRA_FILTER_ID)
            issues_list = jira_api.get_filter(filter_url)

        issues = issues_list.get('issues', [])

        if not issues:
            console.print("[yellow]No issues found matching criteria[/yellow]")
            return

        console.print(f"[green]Found {len(issues)} issues[/green]\n")

        # Show first 20 issues
        table = Table(title=f"Preview: First {min(20, len(issues))} Issues")
        table.add_column("Issue Key", style="cyan")
        table.add_column("Status", style="green")

        for issue in issues[:20]:
            key = issue.get('key', 'N/A')

            # Fetch full details for status
            success, info = jira_api.get_issue_info(key)
            status = info['fields']['status']['name'] if success else 'N/A'

            table.add_row(key, status)

        console.print(table)

        if len(issues) > 20:
            console.print(f"\n[yellow]... and {len(issues) - 20} more issues[/yellow]")

        console.print(f"\n[bold]Total issues that would be migrated: {len(issues)}[/bold]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise
