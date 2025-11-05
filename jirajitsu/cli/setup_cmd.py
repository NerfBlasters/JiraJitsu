"""
Interactive setup command for JiraJitsu
"""
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
import sys
import os
from pathlib import Path
import re
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

console = Console()


def load_env_config(env_path: Path) -> dict:
    """
    Load existing .env configuration file.
    Returns a dictionary of key-value pairs.
    """
    config = {}
    if not env_path.exists():
        return config

    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load .env file: {e}[/yellow]")

    return config


def load_yaml_config(config_path: Path) -> dict:
    """
    Load existing config.yml configuration file.
    Returns a dictionary of configuration values.
    """
    config = {}
    if not config_path.exists():
        return config

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load config.yml file: {e}[/yellow]")

    return config


def normalize_url(url: str) -> str:
    """
    Normalize a URL by fixing common issues:
    - Remove duplicate protocols (http://http:// -> http://)
    - Strip whitespace
    - Ensure proper protocol prefix
    """
    url = url.strip()

    # Fix duplicate protocols (http://http:// or https://https://)
    url = re.sub(r'^(https?://)+(https?://)+', r'\1', url)
    url = re.sub(r'^(https?://)(https?://)+', r'\1', url)

    # If no protocol, assume http://
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    return url


@click.command()
@click.pass_context
def setup(ctx):
    """
    Interactive setup wizard for JiraJitsu

    Configure JIRA and JitBit connections, directories, and settings.
    """

    console.print("[bold blue]JiraJitsu Interactive Setup[/bold blue]\n")

    # Determine paths
    base_dir = Path(__file__).parent.parent.parent
    env_path = base_dir / '.env'
    config_dir = base_dir / 'config'
    config_path = config_dir / 'config.yml'

    # Load existing configuration if it exists
    existing_env = {}
    existing_config = {}
    config_exists = env_path.exists() and config_path.exists()

    if config_exists:
        console.print("[yellow]Configuration files already exist[/yellow]")
        if not Confirm.ask("Update existing configuration?", default=True):
            console.print("[yellow]Setup cancelled[/yellow]")
            return

        # Load existing values to use as defaults
        existing_env = load_env_config(env_path)
        existing_config = load_yaml_config(config_path)
        console.print("This wizard will help you update your JiraJitsu configuration.\n")
        console.print("[dim]Press Enter to keep current values shown in brackets[/dim]\n")
    else:
        console.print("This wizard will help you configure JiraJitsu for first-time use.\n")

    console.print()

    # Collect JIRA configuration
    console.print("[bold cyan]JIRA Configuration[/bold cyan]")
    jira_url_default = existing_env.get('JIRA_API_URL', 'https://your-jira.com/rest/api/2')
    jira_url_raw = Prompt.ask("JIRA API URL", default=jira_url_default)
    jira_url = normalize_url(jira_url_raw)
    if jira_url != jira_url_raw:
        console.print(f"[yellow]URL normalized to: {jira_url}[/yellow]")

    jira_auth_method = Prompt.ask(
        "JIRA Authentication method",
        choices=["basic", "token"],
        default=existing_env.get('JIRA_AUTH_METHOD', 'basic')
    )

    # Check if critical settings changed (require re-entering credentials)
    jira_url_changed = existing_env.get('JIRA_API_URL') and jira_url != existing_env.get('JIRA_API_URL')
    jira_auth_changed = existing_env.get('JIRA_AUTH_METHOD') and jira_auth_method != existing_env.get('JIRA_AUTH_METHOD')

    if jira_auth_method == "basic":
        jira_user_default = existing_env.get('JIRA_USER', '')
        jira_user = Prompt.ask("JIRA Username", default=jira_user_default) if jira_user_default else Prompt.ask("JIRA Username")

        # Only prompt for password if credentials changed or no existing password
        if jira_url_changed or jira_auth_changed or not existing_env.get('JIRA_PWD') or jira_user != existing_env.get('JIRA_USER'):
            jira_pwd = Prompt.ask("JIRA Password", password=True)
        else:
            if Confirm.ask("Keep existing password?", default=True):
                jira_pwd = existing_env.get('JIRA_PWD', '')
            else:
                jira_pwd = Prompt.ask("JIRA Password", password=True)
        jira_token = ""
    else:
        console.print("[yellow]For JIRA Cloud: use email as username with API token[/yellow]")
        console.print("[yellow]For JIRA Server/DC: use Personal Access Token (leave username empty)[/yellow]")

        # If switching FROM basic auth, don't use old username as default
        if jira_auth_changed and existing_env.get('JIRA_AUTH_METHOD') == 'basic':
            console.print("[dim]Tip: Press Enter to leave username empty for PAT, or type email for Cloud[/dim]")
            jira_user = Prompt.ask("JIRA Username/Email (empty for PAT)", default="")
        else:
            jira_user_default = existing_env.get('JIRA_USER', '')
            jira_user = Prompt.ask("JIRA Username/Email (empty for PAT)", default=jira_user_default)

        # Only prompt for token if credentials changed or no existing token
        if jira_url_changed or jira_auth_changed or not existing_env.get('JIRA_TOKEN') or jira_user != existing_env.get('JIRA_USER'):
            jira_token = Prompt.ask("JIRA API Token or Personal Access Token", password=True)
        else:
            if Confirm.ask("Keep existing token?", default=True):
                jira_token = existing_env.get('JIRA_TOKEN', '')
            else:
                jira_token = Prompt.ask("JIRA API Token or Personal Access Token", password=True)
        jira_pwd = ""

    jira_filter_id = Prompt.ask("JIRA Filter ID for migration", default=str(existing_config.get('jira_filter_id', '10000')))
    jira_tag_field = Prompt.ask("JIRA custom field for tags", default=existing_config.get('jira_tag_field', 'customfield_10800'))

    console.print()

    # Collect JitBit configuration
    console.print("[bold cyan]JitBit Configuration[/bold cyan]")
    jitbit_url_default = existing_env.get('JITBIT_API_URL', 'https://your-company.jitbit.com/helpdesk/api')
    jitbit_url_raw = Prompt.ask("JitBit API URL", default=jitbit_url_default)
    jitbit_url = normalize_url(jitbit_url_raw)
    if jitbit_url != jitbit_url_raw:
        console.print(f"[yellow]URL normalized to: {jitbit_url}[/yellow]")

    jitbit_auth_method = Prompt.ask(
        "JitBit Authentication method",
        choices=["basic", "token"],
        default=existing_env.get('JITBIT_AUTH_METHOD', 'basic')
    )

    # Check if critical settings changed (require re-entering credentials)
    jitbit_url_changed = existing_env.get('JITBIT_API_URL') and jitbit_url != existing_env.get('JITBIT_API_URL')
    jitbit_auth_changed = existing_env.get('JITBIT_AUTH_METHOD') and jitbit_auth_method != existing_env.get('JITBIT_AUTH_METHOD')

    if jitbit_auth_method == "basic":
        jitbit_user_default = existing_env.get('JITBIT_USER', '')
        jitbit_user = Prompt.ask("JitBit Username", default=jitbit_user_default) if jitbit_user_default else Prompt.ask("JitBit Username")

        # Only prompt for password if credentials changed or no existing password
        if jitbit_url_changed or jitbit_auth_changed or not existing_env.get('JITBIT_PWD') or jitbit_user != existing_env.get('JITBIT_USER'):
            jitbit_pwd = Prompt.ask("JitBit Password", password=True)
        else:
            if Confirm.ask("Keep existing password?", default=True):
                jitbit_pwd = existing_env.get('JITBIT_PWD', '')
            else:
                jitbit_pwd = Prompt.ask("JitBit Password", password=True)
        jitbit_token = ""
    else:
        console.print("[yellow]Generate API token in JitBit: Admin → API Settings[/yellow]")

        # If switching FROM basic auth, don't use old username as default
        if jitbit_auth_changed and existing_env.get('JITBIT_AUTH_METHOD') == 'basic':
            console.print("[dim]Tip: Press Enter to leave username empty if token is sufficient[/dim]")
            jitbit_user = Prompt.ask("JitBit Username/Email (optional)", default="")
        else:
            jitbit_user_default = existing_env.get('JITBIT_USER', '')
            jitbit_user = Prompt.ask("JitBit Username/Email (optional)", default=jitbit_user_default)

        # Only prompt for token if credentials changed or no existing token
        if jitbit_url_changed or jitbit_auth_changed or not existing_env.get('JITBIT_TOKEN') or jitbit_user != existing_env.get('JITBIT_USER'):
            jitbit_token = Prompt.ask("JitBit API Token", password=True)
        else:
            if Confirm.ask("Keep existing token?", default=True):
                jitbit_token = existing_env.get('JITBIT_TOKEN', '')
            else:
                jitbit_token = Prompt.ask("JitBit API Token", password=True)
        jitbit_pwd = ""

    jitbit_category_default = str(existing_config.get('jitbit_migrate_category_id', '10000'))
    jitbit_category = Prompt.ask("JitBit migration category ID", default=jitbit_category_default)

    jitbit_delete_default = str(existing_config.get('jitbit_delete_category_id', ''))
    jitbit_delete_category = Prompt.ask("JitBit deleted items category ID (optional)", default=jitbit_delete_default)

    jitbit_email_default = existing_config.get('jitbit_default_assign_email', 'admin@yourcompany.com')
    jitbit_default_email = Prompt.ask("Default assignee email", default=jitbit_email_default)

    console.print()

    # Collect directory configuration
    console.print("[bold cyan]Directory Configuration[/bold cyan]")
    attachment_folder_default = existing_config.get('attachment_folder', str(base_dir / "attachments"))
    attachment_folder = Prompt.ask("Attachment storage folder", default=attachment_folder_default)

    log_dir_default = existing_config.get('log_dir', str(base_dir / "logs"))
    log_dir = Prompt.ask("Log directory", default=log_dir_default)

    # Attachment fetch mode
    fetch_mode = Prompt.ask(
        "Attachment fetch mode",
        choices=["NEW_ONLY", "DELETE_REFETCH"],
        default=existing_config.get('fetch_attachments', 'NEW_ONLY')
    )

    console.print()

    # Create directories
    console.print("[cyan]Creating directories...[/cyan]")
    Path(attachment_folder).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    console.print("[green]✓ Directories created[/green]\n")

    # Write .env file
    console.print("[cyan]Writing .env file...[/cyan]")
    env_content = f"""# JiraJitsu Environment Configuration
# Generated by setup wizard

# JitBit API Credentials
JITBIT_API_URL={jitbit_url}
JITBIT_AUTH_METHOD={jitbit_auth_method}
JITBIT_USER={jitbit_user}
JITBIT_PWD={jitbit_pwd}
JITBIT_TOKEN={jitbit_token}

# JIRA API Credentials
JIRA_API_URL={jira_url}
JIRA_AUTH_METHOD={jira_auth_method}
JIRA_USER={jira_user}
JIRA_PWD={jira_pwd}
JIRA_TOKEN={jira_token}
"""

    with open(env_path, 'w') as f:
        f.write(env_content)

    console.print(f"[green]✓ Created {env_path}[/green]\n")

    # Write config.yml file
    console.print("[cyan]Writing config.yml file...[/cyan]")
    config_content = f"""# JiraJitsu Configuration File
# Generated by setup wizard

# Logging Configuration
log_dir: {log_dir}
log_max_bytes: 10485760
log_backup_count: 5

# JitBit Settings
jitbit_migrate_category_id: {jitbit_category}
{f'jitbit_delete_category_id: {jitbit_delete_category}' if jitbit_delete_category else '# jitbit_delete_category_id: 12346'}
jitbit_default_assign_email: {jitbit_default_email}

# JIRA Settings
jira_filter_id: {jira_filter_id}
jira_tag_field: {jira_tag_field}

# Attachment Settings
fetch_attachments: {fetch_mode}
attachment_folder: {attachment_folder}
"""

    with open(config_path, 'w') as f:
        f.write(config_content)

    console.print(f"[green]✓ Created {config_path}[/green]\n")

    # Test connections
    if Confirm.ask("Test API connections now?", default=True):
        console.print("\n[cyan]Testing connections...[/cyan]\n")

        # Import here to use new config
        try:
            # Reload config module to pick up new settings
            import importlib
            from jirajitsu import config as cfg
            importlib.reload(cfg)

            from jirajitsu.jira_api import JiraApi
            from jirajitsu.jitbit_api import JitbitApi
            from jirajitsu.log_handler import LogHandler

            LogHandler(log_level='INFO')

            # Test JIRA
            console.print("[cyan]Testing JIRA connection...[/cyan]")
            jira_api = JiraApi()
            if jira_api.check_url_and_user():
                console.print("[green]✓ JIRA connection successful[/green]")
            else:
                console.print("[red]✗ JIRA connection failed[/red]")

            # Test JitBit
            console.print("[cyan]Testing JitBit connection...[/cyan]")
            jitbit_api = JitbitApi()
            if jitbit_api.check_url_and_user():
                console.print("[green]✓ JitBit connection successful[/green]")
            else:
                console.print("[red]✗ JitBit connection failed[/red]")

        except Exception as e:
            console.print(f"[red]Error testing connections: {str(e)}[/red]")
            console.print("[yellow]You can run 'jirajitsu validate config' later to test[/yellow]")

    console.print("\n[bold green]✓ Setup complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run 'jirajitsu validate config' to verify configuration")
    console.print("  2. Run 'jirajitsu list projects' to see available projects")
    console.print("  3. Run 'jirajitsu validate users' to check user mappings")
    console.print("  4. Run 'jirajitsu test --issue ISSUE-KEY' to test migration")
    console.print("  5. Run 'jirajitsu migrate' to start full migration")
