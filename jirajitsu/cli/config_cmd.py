"""
Configuration management commands for JiraJitsu
"""
import click
from rich.console import Console
from rich.table import Table
import sys
import os
from pathlib import Path
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu import config
from jirajitsu.jira_api import JiraApi
from jirajitsu.jitbit_api import JitbitApi
from jirajitsu.log_handler import LogHandler

console = Console()


@click.group()
@click.pass_context
def config_cmd(ctx):
    """
    Configuration management commands

    View, update, and validate configuration settings.
    """
    pass


@config_cmd.command('view')
@click.option('--show-secrets', is_flag=True, help='Show actual passwords (use with caution)')
@click.pass_context
def view_config(ctx, show_secrets):
    """
    Display current configuration

    Shows all configuration values (passwords masked by default).
    """

    console.print("[bold blue]JiraJitsu Configuration[/bold blue]\n")

    def mask_secret(value):
        if show_secrets or not value:
            return value
        return '*' * min(len(str(value)), 12) + '...'

    # JIRA Settings
    table = Table(title="JIRA Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("JIRA_API_URL", config.JIRA_API_URL)
    table.add_row("JIRA_USER", config.JIRA_USER)
    table.add_row("JIRA_PWD", mask_secret(config.JIRA_PWD))
    table.add_row("JIRA_FILTER_ID", str(config.JIRA_FILTER_ID))
    table.add_row("JIRA_TAG_FIELD", config.JIRA_TAG_FIELD)

    console.print(table)
    console.print()

    # JitBit Settings
    table = Table(title="JitBit Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("JITBIT_API_URL", config.JITBIT_API_URL)
    table.add_row("JITBIT_USER", config.JITBIT_USER)
    table.add_row("JITBIT_PWD", mask_secret(config.JITBIT_PWD))
    table.add_row("JITBIT_MIGRATE_CATEGORY_ID", str(config.JITBIT_MIGRATE_CATEGORY_ID))
    if config.JITBIT_DELETE_CATEGORY_ID:
        table.add_row("JITBIT_DELETE_CATEGORY_ID", str(config.JITBIT_DELETE_CATEGORY_ID))
    table.add_row("JITBIT_DEFAULT_ASSIGN_EMAIL", config.JITBIT_DEFAULT_ASSIGN_EMAIL)

    console.print(table)
    console.print()

    # Other Settings
    table = Table(title="Other Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("ATTACHMENT_FOLDER", config.ATTACHMENT_FOLDER)
    table.add_row("FETCH_ATTACHMENTS", config.FETCH_ATTACHMENTS)
    table.add_row("LOG_DIR", config.LOG_DIR)
    table.add_row("LOG_MAX_BYTES", str(config.LOG_MAX_BYTES))
    table.add_row("LOG_BACKUP_COUNT", str(config.LOG_BACKUP_COUNT))

    console.print(table)

    if not show_secrets:
        console.print("\n[yellow]Passwords are masked. Use --show-secrets to display them.[/yellow]")


@config_cmd.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def set_config(ctx, key, value):
    """
    Update a configuration value

    Updates values in .env or config.yml as appropriate.

    Examples:
        jirajitsu config set jira_filter_id 10001
        jirajitsu config set jira_tag_field customfield_10800
        jirajitsu config set JIRA_USER myuser
    """

    console.print(f"[bold blue]Updating Configuration[/bold blue]\n")

    # Determine which file to update
    env_keys = ['JIRA_API_URL', 'JIRA_USER', 'JIRA_PWD', 'JIRA_TOKEN', 'JIRA_AUTH_METHOD',
                'JITBIT_API_URL', 'JITBIT_USER', 'JITBIT_PWD', 'JITBIT_TOKEN', 'JITBIT_AUTH_METHOD']

    yaml_keys = ['jira_filter_id', 'jira_tag_field', 'jitbit_migrate_category_id',
                 'jitbit_delete_category_id', 'jitbit_default_assign_email',
                 'fetch_attachments', 'attachment_folder', 'log_dir',
                 'log_max_bytes', 'log_backup_count']

    base_dir = Path(__file__).parent.parent.parent
    env_path = base_dir / '.env'
    config_path = base_dir / 'config' / 'config.yml'

    # Normalize key to lowercase for yaml comparison
    key_lower = key.lower()

    if key.upper() in env_keys:
        # Update .env file
        if not env_path.exists():
            console.print(f"[red].env file not found at {env_path}[/red]")
            console.print("[yellow]Run 'jirajitsu setup' first[/yellow]")
            sys.exit(1)

        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update or add the key
        key_found = False
        new_lines = []
        key_upper = key.upper()
        for line in lines:
            if line.strip().startswith(f'{key_upper}='):
                new_lines.append(f'{key_upper}={value}\n')
                key_found = True
            else:
                new_lines.append(line)

        if not key_found:
            new_lines.append(f'\n{key_upper}={value}\n')

        # Write back
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        console.print(f"[green]✓ Updated {key_upper} in .env[/green]")
        console.print("[yellow]Note: Restart required for changes to take effect[/yellow]")

    elif key_lower in yaml_keys:
        # Update config.yml file
        if not config_path.exists():
            console.print(f"[red]config.yml file not found at {config_path}[/red]")
            console.print("[yellow]Run 'jirajitsu setup' first[/yellow]")
            sys.exit(1)

        # Read current config.yml
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}

        # Convert value to appropriate type
        yaml_value = value
        if key_lower in ['jira_filter_id', 'jitbit_migrate_category_id', 'jitbit_delete_category_id',
                         'log_max_bytes', 'log_backup_count']:
            try:
                yaml_value = int(value)
            except ValueError:
                console.print(f"[red]Error: {key} requires an integer value[/red]")
                sys.exit(1)

        # Update the value
        config_data[key_lower] = yaml_value

        # Write back
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        console.print(f"[green]✓ Updated {key_lower} in config.yml[/green]")
        console.print(f"[cyan]New value: {yaml_value}[/cyan]")

    else:
        console.print(f"[red]Unknown configuration key: {key}[/red]")
        console.print("\n[cyan]Valid .env keys:[/cyan]")
        for k in env_keys:
            console.print(f"  - {k}")
        console.print("\n[cyan]Valid config.yml keys:[/cyan]")
        for k in yaml_keys:
            console.print(f"  - {k}")
        sys.exit(1)


@config_cmd.command('validate')
@click.pass_context
def validate_config_cmd(ctx):
    """
    Validate configuration and test connections

    Alias for 'jirajitsu validate config'.
    """

    # Import and call the validate config command
    from .validate_cmd import validate_config
    ctx.invoke(validate_config)


@config_cmd.command('export')
@click.option('--output', type=click.Path(), default='jirajitsu-config-export.txt', help='Output file')
@click.pass_context
def export_config(ctx, output):
    """
    Export current configuration to a file

    Creates a backup of current configuration (passwords masked).
    """

    console.print(f"[bold blue]Exporting Configuration[/bold blue]\n")

    export_content = f"""# JiraJitsu Configuration Export
# Generated configuration snapshot

[JIRA Configuration]
JIRA_API_URL={config.JIRA_API_URL}
JIRA_USER={config.JIRA_USER}
JIRA_PWD=***MASKED***
JIRA_FILTER_ID={config.JIRA_FILTER_ID}
JIRA_TAG_FIELD={config.JIRA_TAG_FIELD}

[JitBit Configuration]
JITBIT_API_URL={config.JITBIT_API_URL}
JITBIT_USER={config.JITBIT_USER}
JITBIT_PWD=***MASKED***
JITBIT_MIGRATE_CATEGORY_ID={config.JITBIT_MIGRATE_CATEGORY_ID}
JITBIT_DELETE_CATEGORY_ID={config.JITBIT_DELETE_CATEGORY_ID if config.JITBIT_DELETE_CATEGORY_ID else 'Not set'}
JITBIT_DEFAULT_ASSIGN_EMAIL={config.JITBIT_DEFAULT_ASSIGN_EMAIL}

[Directories]
ATTACHMENT_FOLDER={config.ATTACHMENT_FOLDER}
LOG_DIR={config.LOG_DIR}

[Settings]
FETCH_ATTACHMENTS={config.FETCH_ATTACHMENTS}
LOG_MAX_BYTES={config.LOG_MAX_BYTES}
LOG_BACKUP_COUNT={config.LOG_BACKUP_COUNT}
"""

    with open(output, 'w') as f:
        f.write(export_content)

    console.print(f"[green]✓ Configuration exported to: {output}[/green]")
    console.print("[yellow]Note: Passwords are masked in export[/yellow]")


@config_cmd.command('test-connection')
@click.option('--system', type=click.Choice(['jira', 'jitbit', 'both']), default='both', help='Which system to test')
@click.pass_context
def test_connection(ctx, system):
    """
    Test API connections

    Verify that JIRA and/or JitBit APIs are accessible.
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    console.print("[bold blue]Testing API Connections[/bold blue]\n")

    success = True

    if system in ['jira', 'both']:
        console.print("[cyan]Testing JIRA connection...[/cyan]")
        try:
            jira_api = JiraApi()
            if jira_api.check_url_and_user():
                console.print("[green]✓ JIRA connection successful[/green]\n")
            else:
                console.print("[red]✗ JIRA connection failed[/red]\n")
                success = False
        except Exception as e:
            console.print(f"[red]✗ JIRA error: {str(e)}[/red]\n")
            success = False

    if system in ['jitbit', 'both']:
        console.print("[cyan]Testing JitBit connection...[/cyan]")
        try:
            jitbit_api = JitbitApi()
            if jitbit_api.check_url_and_user():
                console.print("[green]✓ JitBit connection successful[/green]\n")
            else:
                console.print("[red]✗ JitBit connection failed[/red]\n")
                success = False
        except Exception as e:
            console.print(f"[red]✗ JitBit error: {str(e)}[/red]\n")
            success = False

    if success:
        console.print("[bold green]All connections successful![/bold green]")
    else:
        console.print("[bold red]Some connections failed. Check configuration.[/bold red]")
        sys.exit(1)
