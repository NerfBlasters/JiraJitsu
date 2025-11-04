"""
List/Enumeration commands for JiraJitsu
"""
import click
from rich.console import Console
from rich.table import Table
from tabulate import tabulate
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu.jira_api import JiraApi
from jirajitsu.jitbit_api import JitbitApi
from jirajitsu.log_handler import LogHandler

console = Console()


@click.group(name='list')
@click.pass_context
def list_cmd(ctx):
    """
    List and enumerate JIRA/JitBit resources

    View projects, issue types, categories, filters, and more.
    """
    pass


@list_cmd.command('projects')
@click.option('--count/--no-count', default=True, help='Include issue counts')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list_projects(ctx, count, format):
    """List all JIRA projects with issue counts"""

    # Initialize logging
    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    try:
        jira_api = JiraApi()

        console.print("[bold blue]Fetching JIRA projects...[/bold blue]")
        projects = jira_api.get_projects()

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        # Build data with optional counts
        data = []
        for project in projects:
            row = {
                'Key': project.get('key', 'N/A'),
                'Name': project.get('name', 'N/A'),
                'Lead': project.get('lead', {}).get('displayName', 'N/A')
            }

            if count:
                with console.status(f"Counting issues in {project['key']}..."):
                    issue_count = jira_api.get_project_issue_count(project['key'])
                    row['Issues'] = issue_count

            data.append(row)

        # Output in requested format
        if format == 'table':
            table = Table(title="JIRA Projects")
            for key in data[0].keys():
                table.add_column(key, style="cyan")

            for row in data:
                table.add_row(*[str(v) for v in row.values()])

            console.print(table)

        elif format == 'json':
            import json
            click.echo(json.dumps(data, indent=2))

        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            click.echo(output.getvalue())

        console.print(f"\n[green]Total projects: {len(projects)}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@list_cmd.command('issue-types')
@click.option('--count/--no-count', default=True, help='Include issue counts')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list_issue_types(ctx, count, format):
    """List all JIRA issue types with counts"""

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    try:
        jira_api = JiraApi()

        console.print("[bold blue]Fetching JIRA issue types...[/bold blue]")
        issue_types = jira_api.get_issue_types()

        if not issue_types:
            console.print("[yellow]No issue types found[/yellow]")
            return

        data = []
        for issue_type in issue_types:
            row = {
                'ID': issue_type.get('id', 'N/A'),
                'Name': issue_type.get('name', 'N/A'),
                'Description': issue_type.get('description', 'N/A')
            }

            if count:
                with console.status(f"Counting {issue_type['name']} issues..."):
                    issue_count = jira_api.get_issue_type_count(issue_type['name'])
                    row['Count'] = issue_count

            data.append(row)

        # Output
        if format == 'table':
            table = Table(title="JIRA Issue Types")
            for key in data[0].keys():
                table.add_column(key, style="cyan")

            for row in data:
                table.add_row(*[str(v) for v in row.values()])

            console.print(table)

        elif format == 'json':
            import json
            click.echo(json.dumps(data, indent=2))

        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            click.echo(output.getvalue())

        console.print(f"\n[green]Total issue types: {len(issue_types)}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@list_cmd.command('jitbit-categories')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list_jitbit_categories(ctx, format):
    """List all JitBit categories"""

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    try:
        jitbit_api = JitbitApi()

        console.print("[bold blue]Fetching JitBit categories...[/bold blue]")
        categories = jitbit_api.get_categories()

        if not categories:
            console.print("[yellow]No categories found[/yellow]")
            return

        data = []
        for cat in categories:
            data.append({
                'Category ID': cat.get('CategoryID', 'N/A'),
                'Name': cat.get('Name', 'N/A'),
                'Private': 'Yes' if cat.get('IsPrivate', False) else 'No'
            })

        # Output
        if format == 'table':
            table = Table(title="JitBit Categories")
            table.add_column("Category ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Private", style="yellow")

            for row in data:
                table.add_row(str(row['Category ID']), row['Name'], row['Private'])

            console.print(table)

        elif format == 'json':
            import json
            click.echo(json.dumps(data, indent=2))

        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            click.echo(output.getvalue())

        console.print(f"\n[green]Total categories: {len(categories)}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise


@list_cmd.command('filters')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), default='table', help='Output format')
@click.pass_context
def list_filters(ctx, format):
    """List all JIRA filters accessible to the current user"""

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    try:
        jira_api = JiraApi()

        console.print("[bold blue]Fetching JIRA filters...[/bold blue]")
        filters = jira_api.get_filters()

        if not filters:
            console.print("[yellow]No filters found[/yellow]")
            return

        data = []
        for f in filters:
            data.append({
                'ID': f.get('id', 'N/A'),
                'Name': f.get('name', 'N/A'),
                'Owner': f.get('owner', {}).get('displayName', 'N/A'),
                'Favorite': 'Yes' if f.get('favourite', False) else 'No'
            })

        # Output
        if format == 'table':
            table = Table(title="JIRA Filters")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Owner", style="yellow")
            table.add_column("Favorite", style="magenta")

            for row in data:
                table.add_row(str(row['ID']), row['Name'], row['Owner'], row['Favorite'])

            console.print(table)

        elif format == 'json':
            import json
            click.echo(json.dumps(data, indent=2))

        elif format == 'csv':
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            click.echo(output.getvalue())

        console.print(f"\n[green]Total filters: {len(filters)}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise
