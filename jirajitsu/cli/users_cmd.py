"""
User management commands for JiraJitsu
"""
import click
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu.jira_api import JiraApi
from jirajitsu.jitbit_api import JitbitApi
from jirajitsu.log_handler import LogHandler

console = Console()


@click.group()
@click.pass_context
def users(ctx):
    """
    User management commands

    Sync, validate, and create users between JIRA and JitBit.
    """
    pass


@users.command('sync')
@click.option('--dry-run', is_flag=True, help='Show what would be created without creating')
@click.option('--technician/--no-technician', default=False, help='Create users as technicians')
@click.pass_context
def sync_users(ctx, dry_run, technician):
    """
    Sync all JIRA users to JitBit

    Create any missing users in JitBit.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print("[bold blue]Syncing Users from JIRA to JitBit[/bold blue]\n")

    if dry_run:
        console.print("[yellow]DRY RUN MODE - No users will be created[/yellow]\n")

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

        # Find missing users
        missing_users = []
        for jira_user in jira_users:
            email = jira_user.get('emailAddress', '').lower()
            if email and email not in jitbit_emails:
                missing_users.append(jira_user)

        if not missing_users:
            console.print("[green]All JIRA users already exist in JitBit![/green]")
            return

        console.print(f"[yellow]Found {len(missing_users)} users to create[/yellow]\n")

        created_count = 0
        failed_count = 0

        with Progress() as progress:
            task = progress.add_task("[cyan]Creating users...", total=len(missing_users))

            for user in missing_users:
                email = user.get('emailAddress', '')
                display_name = user.get('displayName', '')

                # Parse name
                name_parts = display_name.split()
                first_name = name_parts[0] if len(name_parts) > 0 else display_name
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                if dry_run:
                    console.print(f"[yellow]Would create: {display_name} ({email})[/yellow]")
                    created_count += 1
                else:
                    try:
                        user_id = jitbit_api.create_user(email, first_name, last_name, is_technician=technician)
                        if user_id > 0:
                            console.print(f"[green]Created: {display_name} ({email}) - ID: {user_id}[/green]")
                            created_count += 1
                        else:
                            console.print(f"[red]Failed to create: {email}[/red]")
                            failed_count += 1
                    except Exception as e:
                        console.print(f"[red]Error creating {email}: {str(e)}[/red]")
                        failed_count += 1

                progress.advance(task)

        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Users {'would be' if dry_run else ''} created: {created_count}")
        if not dry_run and failed_count > 0:
            console.print(f"[red]Failed: {failed_count}[/red]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@users.command('validate')
@click.option('--output', type=click.Path(), help='Save report to CSV file')
@click.pass_context
def validate_users_cmd(ctx, output):
    """
    Validate JIRA to JitBit user mappings

    Check which users exist, missing, and technician status.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print("[bold blue]Validating User Mappings[/bold blue]\n")

    try:
        jira_api = JiraApi()
        jitbit_api = JitbitApi()

        # Fetch users
        console.print("[cyan]Fetching users from both systems...[/cyan]")
        jira_users = jira_api.get_all_users()
        jitbit_users = jitbit_api.get_users()
        jitbit_emails = {user.get('Email', '').lower(): user for user in jitbit_users if user.get('Email')}

        # Validate
        report = []
        stats = {'exists': 0, 'missing': 0, 'no_email': 0, 'technician': 0, 'non_technician': 0}

        for jira_user in jira_users:
            email = jira_user.get('emailAddress', '').lower()
            display_name = jira_user.get('displayName', 'N/A')

            if not email:
                stats['no_email'] += 1
                report.append({
                    'JIRA User': display_name,
                    'Email': 'N/A',
                    'JitBit Status': 'No Email',
                    'Technician': 'N/A'
                })
                continue

            if email in jitbit_emails:
                stats['exists'] += 1
                jitbit_user = jitbit_emails[email]
                is_tech = jitbit_user.get('IsTech', False)  # Fixed: API returns 'IsTech' not 'IsTechie'

                if is_tech:
                    stats['technician'] += 1
                else:
                    stats['non_technician'] += 1

                report.append({
                    'JIRA User': display_name,
                    'Email': email,
                    'JitBit Status': 'Exists',
                    'Technician': 'Yes' if is_tech else 'No'
                })
            else:
                stats['missing'] += 1
                report.append({
                    'JIRA User': display_name,
                    'Email': email,
                    'JitBit Status': 'Missing',
                    'Technician': 'N/A'
                })

        # Display results
        table = Table(title="User Mapping Summary")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Total JIRA Users", str(len(jira_users)))
        table.add_row("Existing in JitBit", str(stats['exists']))
        table.add_row("Missing in JitBit", str(stats['missing']))
        table.add_row("Technicians", str(stats['technician']))
        table.add_row("Non-Technicians", str(stats['non_technician']))
        table.add_row("No Email", str(stats['no_email']))

        console.print(table)

        # Save report if requested
        if output:
            import csv
            with open(output, 'w', newline='') as f:
                if report:
                    writer = csv.DictWriter(f, fieldnames=report[0].keys())
                    writer.writeheader()
                    writer.writerows(report)
            console.print(f"\n[green]Detailed report saved to: {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@users.command('create')
@click.option('--email', required=True, help='User email address')
@click.option('--first-name', required=True, help='User first name')
@click.option('--last-name', required=True, help='User last name')
@click.option('--technician', is_flag=True, help='Create as technician')
@click.pass_context
def create_user(ctx, email, first_name, last_name, technician):
    """
    Create a single user in JitBit

    Manually create a user with specified details.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print(f"[bold blue]Creating JitBit User[/bold blue]\n")

    try:
        jitbit_api = JitbitApi()

        # Check if user already exists
        existing_id = jitbit_api.get_user_id_by_email(email)
        if existing_id > 0:
            console.print(f"[yellow]User already exists with ID: {existing_id}[/yellow]")
            return

        # Create user
        console.print(f"[cyan]Creating user: {first_name} {last_name} ({email})[/cyan]")
        user_id = jitbit_api.create_user(email, first_name, last_name, is_technician=technician)

        if user_id > 0:
            tech_status = "technician" if technician else "regular user"
            console.print(f"[green]✓ Successfully created {tech_status} with ID: {user_id}[/green]")
        else:
            console.print(f"[red]✗ Failed to create user[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise
