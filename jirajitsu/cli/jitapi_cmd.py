"""
Manual JitBit API testing command
"""
import click
from rich.console import Console
from rich.syntax import Syntax
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jirajitsu import config
from jirajitsu.jitbit_api import JitbitApi
from jirajitsu.log_handler import LogHandler

console = Console()


@click.command()
@click.option('--endpoint', required=True, help='JitBit API endpoint (e.g., UserByEmail, ticket, Categories)')
@click.option('--parameter', '-p', multiple=True, nargs=2, metavar='<name> <value>',
              help='Parameter name and value (repeat for multiple parameters)')
@click.option('--method', type=click.Choice(['GET', 'POST'], case_sensitive=False), default='GET',
                help='HTTP method (default: GET)')
@click.pass_context
def jitapi(ctx, endpoint, parameter, method):
    """
    Manual JitBit API testing

    Make direct API calls to JitBit for testing and debugging.

    \b
    Examples:
        jirajitsu jitapi --endpoint UserByEmail --parameter email test@example.com
        jirajitsu jitapi --endpoint ticket --parameter id 12345
        jirajitsu jitapi --endpoint Categories
        jirajitsu jitapi --endpoint CreateUser --method POST --parameter email new@example.com --parameter firstName Test --parameter lastName User
    """

    log_level = ctx.obj.get('LOG_LEVEL', 'INFO')
    LogHandler(log_level=log_level)

    # Ensure endpoint starts with /
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint

    console.print(f"[bold blue]JitBit API Manual Test[/bold blue]\n")

    # Build parameters dictionary
    params = {}
    for name, value in parameter:
        params[name] = value

    # Display request info
    console.print(f"[cyan]Endpoint:[/cyan] {endpoint}")
    console.print(f"[cyan]Method:[/cyan] {method.upper()}")
    if params:
        console.print(f"[cyan]Parameters:[/cyan]")
        for name, value in params.items():
            console.print(f"  {name} = {value}")
    else:
        console.print(f"[cyan]Parameters:[/cyan] None")
    console.print()

    try:
        # Initialize JitBit API
        jitbit_api = JitbitApi()

        # Construct full URL
        full_url = config.JITBIT_API_URL + endpoint

        # Make the API call
        console.print("[cyan]Making API call...[/cyan]\n")

        if method.upper() == 'GET':
            response = jitbit_api._make_request('GET', full_url, params=params)
        else:  # POST
            response = jitbit_api._make_request('POST', full_url, data=params)

        # Display response status
        status_color = "green" if response.status_code < 400 else "red"
        console.print(f"[bold]Response Status:[/bold] [{status_color}]{response.status_code}[/{status_color}]\n")

        # Always display response body
        console.print("[bold]Response Body:[/bold]")

        # Try to parse as JSON for pretty printing
        try:
            json_response = response.json()
            json_str = json.dumps(json_response, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            console.print(syntax)
        except json.JSONDecodeError:
            # Not JSON, display as text
            if response.text:
                console.print(response.text)
            else:
                console.print("[dim](empty response)[/dim]")

        # Exit with error code if request failed
        if response.status_code >= 400:
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)
