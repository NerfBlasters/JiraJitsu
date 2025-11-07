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

    console.print()

    # Migration scoping - configure interactively later after validation
    jira_filter_id = existing_config.get('jira_filter_id', '')
    jira_tag_field = existing_config.get('jira_tag_field', '')

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

    # Create/verify directories with permission checks
    console.print("[bold cyan]Directory Setup[/bold cyan]")

    for dir_path, dir_name in [(attachment_folder, "Attachment folder"),
                                (log_dir, "Log directory"),
                                (str(config_dir), "Config directory")]:
        path_obj = Path(dir_path)
        if path_obj.exists():
            # Check if it's actually a directory
            if not path_obj.is_dir():
                console.print(f"[red]✗ {dir_name}: {dir_path} exists but is not a directory![/red]")
                console.print("[red]Setup cannot continue. Please resolve this conflict.[/red]")
                sys.exit(1)

            # Check write permissions
            if os.access(dir_path, os.W_OK):
                console.print(f"[green]✓ {dir_name}: {dir_path} (exists, writable)[/green]")
            else:
                console.print(f"[red]✗ {dir_name}: {dir_path} (exists, but not writable!)[/red]")
                console.print(f"[yellow]  Please fix permissions: chmod u+w {dir_path}[/yellow]")
                sys.exit(1)
        else:
            # Create directory
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✓ {dir_name}: Created {dir_path}[/green]")
            except PermissionError:
                console.print(f"[red]✗ {dir_name}: Cannot create {dir_path} (permission denied)[/red]")
                sys.exit(1)
            except Exception as e:
                console.print(f"[red]✗ {dir_name}: Cannot create {dir_path} ({e})[/red]")
                sys.exit(1)

    console.print()

    # Backup existing config files if they exist
    if env_path.exists() or config_path.exists():
        if Confirm.ask("Backup existing configuration files (.env, config.yml) as *.bak?", default=True):
            console.print("[cyan]Creating backups...[/cyan]")

            if env_path.exists():
                backup_path = env_path.with_suffix('.env.bak')
                try:
                    import shutil
                    shutil.copy2(env_path, backup_path)
                    console.print(f"[green]✓ Backed up .env → {backup_path.name}[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠ Could not backup .env: {e}[/yellow]")

            if config_path.exists():
                backup_path = config_path.with_suffix('.yml.bak')
                try:
                    import shutil
                    shutil.copy2(config_path, backup_path)
                    console.print(f"[green]✓ Backed up config.yml → {backup_path.name}[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠ Could not backup config.yml: {e}[/yellow]")

            console.print()

    # Write .env file
    env_action = "Updating" if env_path.exists() else "Creating"
    console.print(f"[cyan]{env_action} .env file...[/cyan]")
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

    env_result = "Updated" if env_action == "Updating" else "Created"
    console.print(f"[green]✓ {env_result} {env_path}[/green]\n")

    # Write config.yml file
    config_action = "Updating" if config_path.exists() else "Creating"
    console.print(f"[cyan]{config_action} config.yml file...[/cyan]")

    # Build JIRA settings section
    jira_settings_lines = []
    if jira_filter_id:
        jira_settings_lines.append(f"jira_filter_id: {jira_filter_id}")
    else:
        jira_settings_lines.append("# jira_filter_id: 10000  # Set this to scope migration to specific filter")

    if jira_tag_field:
        jira_settings_lines.append(f"jira_tag_field: {jira_tag_field}")
    else:
        jira_settings_lines.append("# jira_tag_field: customfield_10800  # Set this to migrate tags from custom field")

    jira_settings = "\n".join(jira_settings_lines)

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
{jira_settings}

# Attachment Settings
fetch_attachments: {fetch_mode}
attachment_folder: {attachment_folder}
"""

    with open(config_path, 'w') as f:
        f.write(config_content)

    config_result = "Updated" if config_action == "Updating" else "Created"
    console.print(f"[green]✓ {config_result} {config_path}[/green]\n")

    # Test connections
    jira_api = None
    jitbit_api = None
    connections_ok = False

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
            jira_ok = jira_api.check_url_and_user()
            if jira_ok:
                console.print("[green]✓ JIRA connection successful[/green]")
            else:
                console.print("[red]✗ JIRA connection failed[/red]")

            # Test JitBit
            console.print("[cyan]Testing JitBit connection...[/cyan]")
            jitbit_api = JitbitApi()
            jitbit_ok = jitbit_api.check_url_and_user()
            if jitbit_ok:
                console.print("[green]✓ JitBit connection successful[/green]")
            else:
                console.print("[red]✗ JitBit connection failed[/red]")

            connections_ok = jira_ok and jitbit_ok

        except Exception as e:
            console.print(f"[red]Error testing connections: {str(e)}[/red]")
            console.print("[yellow]You can run 'jirajitsu validate config' later to test[/yellow]")

    # Interactive defaults selection (if connections succeeded)
    if connections_ok and Confirm.ask("\nWould you like to select defaults from available options?", default=True):
        console.print("\n[bold cyan]Setting Defaults Interactively[/bold cyan]\n")

        # Update config with selected defaults
        updated_config = {}

        # Select JitBit category
        if Confirm.ask("Select JitBit migration category from list?", default=True):
            try:
                console.print("[cyan]Fetching JitBit categories...[/cyan]")
                categories = jitbit_api.get_categories()

                if categories:
                    console.print("\n[bold]Available Categories:[/bold]")
                    for i, cat in enumerate(categories, 1):
                        private_marker = " [yellow](Private)[/yellow]" if cat.get('IsPrivate') else ""
                        console.print(f"  {i}. {cat.get('Name')}{private_marker} [dim](ID: {cat.get('CategoryID')})[/dim]")

                    while True:
                        choice = Prompt.ask(f"\nSelect category [1-{len(categories)}]", default="1")
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(categories):
                                selected_cat = categories[idx]
                                updated_config['jitbit_migrate_category_id'] = selected_cat['CategoryID']
                                console.print(f"[green]✓ Selected: {selected_cat['Name']} (ID: {selected_cat['CategoryID']})[/green]")
                                break
                            else:
                                console.print(f"[red]Please enter a number between 1 and {len(categories)}[/red]")
                        except ValueError:
                            console.print("[red]Please enter a valid number[/red]")
                else:
                    console.print("[yellow]No categories found[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Could not fetch categories: {e}[/yellow]")

        # Select JIRA filter
        if Confirm.ask("\nSelect JIRA filter from list?", default=not bool(jira_filter_id)):
            try:
                console.print("[cyan]Fetching JIRA filters...[/cyan]")
                filters = jira_api.get_filters()

                if filters:
                    console.print("\n[bold]Available Filters:[/bold]")
                    for i, f in enumerate(filters, 1):
                        fav_marker = " ⭐" if f.get('favourite') else ""
                        console.print(f"  {i}. {f.get('name')}{fav_marker} [dim](ID: {f.get('id')})[/dim]")
                        if f.get('description'):
                            console.print(f"     [dim]{f.get('description')[:80]}[/dim]")

                    console.print(f"\n  0. [dim]Skip - configure later[/dim]")

                    while True:
                        choice = Prompt.ask(f"\nSelect filter [0-{len(filters)}]", default="0")
                        try:
                            idx = int(choice)
                            if idx == 0:
                                console.print("[yellow]Skipped - you can set this later with 'jirajitsu config set jira_filter_id <ID>'[/yellow]")
                                break
                            elif 1 <= idx <= len(filters):
                                selected_filter = filters[idx - 1]
                                updated_config['jira_filter_id'] = selected_filter['id']
                                console.print(f"[green]✓ Selected: {selected_filter['name']} (ID: {selected_filter['id']})[/green]")
                                break
                            else:
                                console.print(f"[red]Please enter a number between 0 and {len(filters)}[/red]")
                        except ValueError:
                            console.print("[red]Please enter a valid number[/red]")
                else:
                    console.print("[yellow]No filters found[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Could not fetch filters: {e}[/yellow]")

        # Select default assignee
        if Confirm.ask("\nSelect default assignee from JitBit users?", default=True):
            try:
                console.print("[cyan]Fetching JitBit users...[/cyan]")
                users = jitbit_api.get_users()

                if users:
                    # Filter to active users only
                    active_users = [u for u in users if not u.get('Disabled', False)]

                    console.print("\n[bold]Available Users:[/bold]")
                    for i, u in enumerate(active_users, 1):
                        admin_marker = " [cyan](Admin)[/cyan]" if u.get('IsAdmin') else ""
                        console.print(f"  {i}. {u.get('FullName')}{admin_marker} - {u.get('Email')} [dim](ID: {u.get('UserID')})[/dim]")

                    while True:
                        choice = Prompt.ask(f"\nSelect default assignee [1-{len(active_users)}]", default="1")
                        try:
                            idx = int(choice) - 1
                            if 0 <= idx < len(active_users):
                                selected_user = active_users[idx]
                                updated_config['jitbit_default_assign_email'] = selected_user['Email']
                                console.print(f"[green]✓ Selected: {selected_user['FullName']} ({selected_user['Email']})[/green]")
                                break
                            else:
                                console.print(f"[red]Please enter a number between 1 and {len(active_users)}[/red]")
                        except ValueError:
                            console.print("[red]Please enter a valid number[/red]")
                else:
                    console.print("[yellow]No users found[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Could not fetch users: {e}[/yellow]")

        # Write updated config if anything changed
        if updated_config:
            console.print("\n[cyan]Updating config.yml with selected defaults...[/cyan]")

            # Reload and merge config
            current_config = load_yaml_config(config_path)
            current_config.update(updated_config)

            # Rebuild config content with updated values
            jira_filter_id = current_config.get('jira_filter_id', jira_filter_id)
            jira_tag_field = current_config.get('jira_tag_field', jira_tag_field)
            jitbit_category = current_config.get('jitbit_migrate_category_id', jitbit_category)
            jitbit_default_email = current_config.get('jitbit_default_assign_email', jitbit_default_email)

            # Rebuild config file
            jira_settings_lines = []
            if jira_filter_id:
                jira_settings_lines.append(f"jira_filter_id: {jira_filter_id}")
            else:
                jira_settings_lines.append("# jira_filter_id: 10000  # Set this to scope migration to specific filter")

            if jira_tag_field:
                jira_settings_lines.append(f"jira_tag_field: {jira_tag_field}")
            else:
                jira_settings_lines.append("# jira_tag_field: customfield_10800  # Set this to migrate tags from custom field")

            jira_settings = "\n".join(jira_settings_lines)

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
jitbit_jira_assignee_field_id: {current_config.get('jitbit_jira_assignee_field_id', 66782)}

# JIRA Settings
{jira_settings}

# Attachment Settings
fetch_attachments: {fetch_mode}
attachment_folder: {attachment_folder}
"""

            with open(config_path, 'w') as f:
                f.write(config_content)

            console.print(f"[green]✓ Updated {config_path}[/green]")

    console.print("\n[bold green]✓ Setup complete![/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Run 'jirajitsu validate config' to verify configuration")
    console.print("  2. Run 'jirajitsu list projects' to see available projects")
    console.print("  3. Run 'jirajitsu list categories' to see JitBit categories")
    console.print("  4. Run 'jirajitsu list filters' to see JIRA filters")
    if not jira_filter_id:
        console.print("     [dim]↳ Then run 'jirajitsu config set jira_filter_id <ID>' to scope migration[/dim]")
    console.print("  5. Run 'jirajitsu validate users' to check user mappings")
    console.print("  6. Run 'jirajitsu test --issue ISSUE-KEY' to test migration")
    console.print("  7. Run 'jirajitsu migrate' to start full migration")
