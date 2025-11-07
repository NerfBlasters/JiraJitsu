"""
Main CLI entry point for JiraJitsu using Click
"""
import click
from rich.console import Console

console = Console()


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-essential output')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              help='Set logging level')
@click.pass_context
def cli(ctx, verbose, quiet, log_level):
    """
    JiraJitsu - JIRA to JitBit Migration Tool

    A comprehensive CLI tool for migrating issues from JIRA to JitBit helpdesk.

    \b
    Common commands:
      setup      - Interactive configuration wizard
      list       - List projects, categories, filters, etc.
      validate   - Validate configuration and users
      migrate    - Migrate issues from JIRA to JitBit
      test       - Test migration of a single issue
      users      - User management commands
      config     - Configuration management
      jitapi     - Manual JitBit API testing

    \b
    Examples:
      jirajitsu setup                              # Interactive setup
      jirajitsu list projects                      # List JIRA projects
      jirajitsu validate users --create-missing    # Validate and create users
      jirajitsu test --issue RFM-123              # Test single issue
      jirajitsu migrate --dry-run                  # Preview migration
      jirajitsu migrate --project RFM --range 100:200  # Migrate range
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options
    ctx.obj['VERBOSE'] = verbose
    ctx.obj['QUIET'] = quiet
    ctx.obj['LOG_LEVEL'] = log_level or ('DEBUG' if verbose else 'INFO' if not quiet else 'WARNING')


# Import subcommand modules
from . import (
    setup_cmd,
    config_cmd,
    list_cmd,
    validate_cmd,
    users_cmd,
    migrate_cmd,
    test_cmd,
    jitapi_cmd
)

# Register subcommands
cli.add_command(setup_cmd.setup)
cli.add_command(config_cmd.config_cmd, name='config')
cli.add_command(list_cmd.list_cmd, name='list')
cli.add_command(validate_cmd.validate)
cli.add_command(users_cmd.users)
cli.add_command(migrate_cmd.migrate)
cli.add_command(test_cmd.test)
cli.add_command(jitapi_cmd.jitapi)


def main():
    """Entry point for console_scripts"""
    cli(obj={})


if __name__ == '__main__':
    main()
