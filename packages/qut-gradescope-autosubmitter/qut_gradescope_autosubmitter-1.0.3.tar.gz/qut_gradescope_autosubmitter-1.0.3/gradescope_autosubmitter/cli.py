"""Command-line interface for Gradescope Auto Submitter."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, List

import click
from dotenv import load_dotenv

from .config import Config
from .core import GradescopeSubmitter
from .rich_console import (
    log_info as log, log_success, log_warning, log_error,
    create_credential_status_table, create_credentials_interface, 
    create_submenu_panel, console, get_colors
)
from rich.live import Live
from rich.prompt import Prompt
from .credentials import get_credentials


# Load .env files: user-level first, then project-level (project overrides user)
def _user_env_path() -> Path:
    if os.name == 'nt':
        return Path.home() / "AppData" / "Local" / "qut_gradescope_autosubmitter" / ".env"
    else:
        return Path.home() / ".qut-gradescope-autosubmitter" / ".env"

user_env = _user_env_path()
if user_env.exists():
    load_dotenv(dotenv_path=user_env)

# Then load project .env if present (overrides user-level values)
load_dotenv()


@click.group(invoke_without_command=True, context_settings={"help_option_names": []})
@click.option('--version', is_flag=True, help='Show version and exit.')
@click.option('--help', is_flag=True, help='Show help and exit.')
@click.pass_context
def cli(ctx, version, help):
    """QUT Gradescope Auto Submitter - Secure automation for QUT students."""
    if version:
        show_version()
        return
    
    if help:
        show_help(ctx)
        return
    
    if ctx.invoked_subcommand is None:
        show_help(ctx)

def show_version():
    """Display version information with Rich formatting."""
    from . import __version__
    from rich.panel import Panel
    from rich import box
    
    colors = get_colors()
    
    content = f"""[bold {colors['primary']}]QUT Gradescope Auto Submitter[/bold {colors['primary']}]
Version: [{colors['success']}]{__version__}[/{colors['success']}]

[dim]Secure automation tool for QUT Gradescope submissions[/dim]
[dim]Repository: https://github.com/danieltsam/qut-gradescope-autosubmitter[/dim]"""
    
    panel = Panel(
        content,
        title="Version Information",
        border_style=colors['primary'],
        box=box.DOUBLE
    )
    
    console.print(panel)

def show_help(ctx):
    """Display help information with Rich formatting."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    colors = get_colors()
    
    # Create main help panel
    content = f"""[bold {colors['primary']}]QUT Gradescope Auto Submitter[/bold {colors['primary']}]

[dim]Secure automation tool for QUT Gradescope submissions.[/dim]
[dim]Automatically bundles files, logs in with QUT SSO, and submits to Gradescope.[/dim]

[bold]Usage:[/bold] [{colors['warning']}]gradescope [OPTIONS] COMMAND [ARGS]...[/{colors['warning']}]"""
    
    help_panel = Panel(
        content,
        title="Help",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    # Create commands table
    commands_table = Table(title="Available Commands", box=box.ROUNDED)
    commands_table.add_column("Command", style=colors['primary'], no_wrap=True)
    commands_table.add_column("Description", style="white")
    
    commands_table.add_row("submit", "Submit assignment to Gradescope")
    commands_table.add_row("credentials", "Manage login credentials") 
    commands_table.add_row("doctor", "Check system requirements")
    commands_table.add_row("init", "Initialize gradescope.yml config")
    commands_table.add_row("validate", "Validate configuration")
    commands_table.add_row("ui", "Customize UI colors and settings")
    commands_table.add_row("hooks", "Set up Git hooks for automation")
    
    # Create options table
    options_table = Table(title="Global Options", box=box.ROUNDED)
    options_table.add_column("Option", style=colors['primary'], no_wrap=True)
    options_table.add_column("Description", style="white")
    
    options_table.add_row("--version", "Show version and exit")
    options_table.add_row("--help", "Show this help message")
    
    console.print(help_panel)
    console.print()
    console.print(commands_table)
    console.print()
    console.print(options_table)
    console.print()
    console.print(f"[dim]For detailed command help: [{colors['primary']}]gradescope COMMAND --help[/{colors['primary']}][/dim]")

def show_submit_help():
    """Display help for the submit command with Rich formatting."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    colors = get_colors()
    
    # Create main help panel
    content = f"""[bold {colors['primary']}]gradescope submit[/bold {colors['primary']}] - Submit files to Gradescope

[dim]Automatically bundles your project files, logs into QUT SSO, navigates to the specified
course and assignment, and submits your files to Gradescope.[/dim]

[bold]Usage:[/bold] [{colors['warning']}]gradescope submit [OPTIONS][/{colors['warning']}]"""
    
    help_panel = Panel(
        content,
        title="Submit Command Help",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    # Create options table
    options_table = Table(title="Options", box=box.ROUNDED)
    options_table.add_column("Option", style=colors['primary'], no_wrap=True)
    options_table.add_column("Description", style="white")
    
    # Basic options
    options_table.add_row("-c, --course", "Course name (e.g., CAB201)")
    options_table.add_row("-a, --assignment", "Assignment name (e.g., Assignment 2)")
    options_table.add_row("-f, --file", "Output zip file name (default: submission.zip)")
    options_table.add_row("-b, --bundle", "File patterns to bundle (can be used multiple times)")
    options_table.add_row("-u, --username", "QUT username (or set GRADESCOPE_USERNAME env var)")
    options_table.add_row("-p, --password", "QUT password (or set GRADESCOPE_PASSWORD env var)")
    
    # Advanced options
    options_table.add_row("--config", "Path to config file")
    options_table.add_row("--headless", "Run browser in headless mode")
    options_table.add_row("--no-grade-wait", "Don't wait for grade to appear")
    options_table.add_row("--fresh-login", "Force fresh login (ignore saved session)")
    options_table.add_row("--manual-login", "Open browser for manual login (maximum security)")
    options_table.add_row("--no-session-save", "Don't save credentials to session env vars")
    
    # Examples table
    examples_table = Table(title="Examples", box=box.ROUNDED)
    examples_table.add_column("Command", style=colors['primary'])
    examples_table.add_column("Description", style="white")
    
    examples_table.add_row("gradescope submit", "Submit using config file settings")
    examples_table.add_row("gradescope submit --headless", "Submit in background (no browser window)")
    examples_table.add_row("gradescope submit -c cab201 -a t6q1", "Override course and assignment")
    examples_table.add_row("gradescope submit -b '*.py' -b '*.txt'", "Submit only Python and text files")
    examples_table.add_row("gradescope submit --manual-login", "Maximum security - login in browser")
    
    console.print(help_panel)
    console.print()
    console.print(options_table)
    console.print()
    console.print(examples_table)
    console.print()

def show_init_help():
    """Display help for the init command with Rich formatting."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    colors = get_colors()
    
    # Create main help panel
    content = f"""[bold {colors['primary']}]gradescope init[/bold {colors['primary']}] - Create configuration file

[dim]Creates a sample gradescope.yml configuration file in the current directory
with default settings that you can customize for your project.[/dim]

[bold]Usage:[/bold] [{colors['warning']}]gradescope init [OPTIONS][/{colors['warning']}]"""
    
    help_panel = Panel(
        content,
        title="Init Command Help",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    # Create options table
    options_table = Table(title="Options", box=box.ROUNDED)
    options_table.add_column("Option", style=colors['primary'], no_wrap=True)
    options_table.add_column("Description", style="white")
    
    options_table.add_row("-p, --path", "Config file path (default: gradescope.yml)")
    
    # Examples table
    examples_table = Table(title="Examples", box=box.ROUNDED)
    examples_table.add_column("Command", style=colors['primary'])
    examples_table.add_column("Description", style="white")
    
    examples_table.add_row("gradescope init", "Create gradescope.yml in current directory")
    examples_table.add_row("gradescope init --path my-config.yml", "Create config with custom filename")
    examples_table.add_row("gradescope init -p ../project.yml", "Create config in parent directory")
    
    console.print(help_panel)
    console.print()
    console.print(options_table)
    console.print()
    console.print(examples_table)
    console.print()

def show_validate_help():
    """Display help for the validate command with Rich formatting."""
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    colors = get_colors()
    
    # Create main help panel
    content = f"""[bold {colors['primary']}]gradescope validate[/bold {colors['primary']}] - Validate configuration

[dim]Checks your gradescope.yml configuration file for errors and displays
a comprehensive status report including credentials, settings, and system requirements.[/dim]

[bold]Usage:[/bold] [{colors['warning']}]gradescope validate [OPTIONS][/{colors['warning']}]"""
    
    help_panel = Panel(
        content,
        title="Validate Command Help",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    # Create options table
    options_table = Table(title="Options", box=box.ROUNDED)
    options_table.add_column("Option", style=colors['primary'], no_wrap=True)
    options_table.add_column("Description", style="white")
    
    options_table.add_row("--config", "Path to config file (default: gradescope.yml)")
    
    # Examples table
    examples_table = Table(title="Examples", box=box.ROUNDED)
    examples_table.add_column("Command", style=colors['primary'])
    examples_table.add_column("Description", style="white")
    
    examples_table.add_row("gradescope validate", "Check default gradescope.yml configuration")
    examples_table.add_row("gradescope validate --config my-config.yml", "Check custom configuration file")
    
    # What it checks section
    checks_content = f"""• Configuration file syntax and required fields
• Course and assignment settings
• File bundling patterns
• Security and behavior settings
• Credential availability (username/password)
• System requirements (Python, Playwright)"""
    
    checks_panel = Panel(
        checks_content,
        title="What Gets Validated",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    console.print(help_panel)
    console.print()
    console.print(options_table)
    console.print()
    console.print(examples_table)
    console.print()
    console.print(checks_panel)
    console.print()


@cli.command()
# Single-character flags first
@click.option('-c', '--course', help='Course name (e.g., CAB201)')
@click.option('-a', '--assignment', help='Assignment name (e.g., Assignment 2)')
@click.option('-f', '--file', 'zip_name', help='Output zip file name (default: submission.zip)')
@click.option('-b', '--bundle', multiple=True, help='File patterns to bundle (can be used multiple times)')
@click.option('-u', '--username', help='QUT username (or set GRADESCOPE_USERNAME env var)')
@click.option('-p', '--password', help='QUT password (or set GRADESCOPE_PASSWORD env var)')
# Double-dash flags
@click.option('--config', help='Path to config file')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--no-grade-wait', is_flag=True, help="Don't wait for grade to appear")
@click.option('--fresh-login', is_flag=True, help='Force fresh login (ignore saved session)')
@click.option('--manual-login', is_flag=True, help='Open browser for manual login (maximum security)')
@click.option('--no-session-save', is_flag=True, help='Don\'t save credentials to session env vars')
@click.option('--help', is_flag=True, help='Show help for this command')
@click.pass_context
def submit(ctx, config, course, assignment, zip_name, bundle, headless, no_grade_wait, fresh_login, manual_login, no_session_save, username, password, help):
    """Submit files to Gradescope."""
    if help:
        show_submit_help()
        return
    
    try:
        # Load configuration
        cfg = Config(config)
        cfg.validate()
        
        # Get parameters from CLI args or config
        course = course or cfg.get('course')
        assignment = assignment or cfg.get('assignment')
        zip_name = zip_name or cfg.get('zip_name', 'submission.zip')
        bundle_patterns = list(bundle) if bundle else cfg.get('bundle', ['*'])
        headless = headless or cfg.get('headless', False)
        notify_when_graded = not no_grade_wait and cfg.get('notify_when_graded', True)
        
        # Check config for always_fresh_login preference
        # Read config values and combine with CLI flags
        config_fresh_login = cfg.get('always_fresh_login', False)
        config_manual_login = cfg.get('manual_login', False)
        config_no_session_save = cfg.get('no_session_save', False)
        
        # Combine CLI flags with config values
        fresh_login = fresh_login or config_fresh_login
        manual_login = manual_login or config_manual_login
        no_session_save = no_session_save or config_no_session_save
        
        # Manual login takes precedence over fresh login
        if manual_login:
            fresh_login = True
        
        if not course or not assignment:
            click.echo("❌ Course and assignment are required. Set them in config file or use --course and --assignment")
            sys.exit(1)
        
        # Handle different credential modes
        if manual_login:
            # Manual login mode - no credentials needed from us
            creds = None
            log("Manual login mode - you'll login in the browser")
        elif username and password:
            # Explicit credentials provided
            creds = (username, password)
            log("Using provided credentials")
        else:
            # Check if credentials are available
            username = os.getenv('GRADESCOPE_USERNAME')
            password = os.getenv('GRADESCOPE_PASSWORD')
            
            if not username or not password:
                colors = get_colors()
                click.echo("❌ No credentials found!")
                click.echo("\nOptions:")
                click.echo("[1] Enter and save to .env (local project file)")
                click.echo("[2] Enter once for this run")
                click.echo("[3] Cancel")

                choice = click.prompt(f"Choose [1/2/3]", type=int, default=1)

                if choice == 1:
                    from .credentials import get_credentials
                    try:
                        creds = get_credentials(set_session_vars=False, persist_to_env=True)
                        log("Using credentials saved to .env")
                    except Exception as e:
                        click.echo(f"❌ Error: {e}")
                        sys.exit(1)
                elif choice == 2:
                    from .credentials import get_credentials
                    try:
                        creds = get_credentials(set_session_vars=False, persist_to_env=False)
                        log("Using one-time credentials")
                    except Exception as e:
                        click.echo(f"❌ Error: {e}")
                        sys.exit(1)
                else:
                    click.echo("\n💡 To set persistent credentials:")
                    click.echo("   Run 'gradescope credentials' to see setup commands")
                    click.echo("   Or set GRADESCOPE_USERNAME and GRADESCOPE_PASSWORD")
                    sys.exit(1)
            else:
                creds = (username, password)
                log("Credentials loaded from environment")
        
        # Create submitter and run submission
        if manual_login:
            # Force non-headless for manual login
            submitter = GradescopeSubmitter(None, None, False, True, manual_login=True)
        else:
            submitter = GradescopeSubmitter(creds[0], creds[1], headless, fresh_login)
        
        submitter.create_zip(bundle_patterns, zip_name)
        
        asyncio.run(submitter.submit_to_gradescope(
            course, assignment, zip_name, notify_when_graded
        ))
        
        
    except (FileNotFoundError, ValueError) as e:
        click.echo(f"\n❌ {e}")
        click.echo("\nSetup Help:")
        click.echo("1. Run 'gradescope init' to create a config file")
        click.echo("2. Run 'gradescope credentials' to see credential setup commands")
        click.echo("3. Set environment variables: GRADESCOPE_USERNAME and GRADESCOPE_PASSWORD")
        click.echo("4. Or use --username and --password flags (less secure)")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nOperation cancelled by user\n")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)


@cli.command()
@click.option('--path', '-p', default='gradescope.yml', help='Config file path (default: gradescope.yml)')
@click.option('--help', is_flag=True, help='Show help for this command')
@click.pass_context
def init(ctx, path, help):
    """Create an example configuration file."""
    if help:
        show_init_help()
        return
    
    from .rich_console import console, get_colors
    
    if Path(path).exists():
        if not click.confirm(f"Config file '{path}' already exists. Overwrite?"):
            return
    
    cfg = Config()
    cfg.create_example_config(path)
    
    colors = get_colors()
    
    from rich.panel import Panel
    from rich import box
    
    content = f"""[{colors['primary']}]1.[/{colors['primary']}] Edit [bold]{path}[/bold] with your course and assignment details
[{colors['primary']}]2.[/{colors['primary']}] Set your credentials: run [bold]gradescope credentials[/bold] to see setup commands  
[{colors['primary']}]3.[/{colors['primary']}] Run: [bold]gradescope submit[/bold]"""
    
    panel = Panel(
        content,
        title="Next Steps",
        border_style=colors['primary'],
        box=box.ROUNDED
    )
    
    console.print(f"\n[{colors['success']}]✓ Created config file: {path}[/{colors['success']}]")
    console.print(panel)
    console.print()


@cli.command()
@click.option('--config', help='Path to config file')
@click.option('--help', is_flag=True, help='Show help for this command')
@click.pass_context
def validate(ctx, config, help):
    """Validate configuration file."""
    if help:
        show_validate_help()
        return
    
    from .rich_console import console, get_colors, log_success, log_error
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    
    try:
        cfg = Config(config)
        cfg.validate()
        colors = get_colors()
        
        log_success("Configuration is valid!")
        
        # Create configuration table
        table = Table(title="Configuration Overview", box=box.ROUNDED)
        table.add_column("Category", style=colors['primary'], no_wrap=True)
        table.add_column("Setting", style=colors['primary'])
        table.add_column("Value", style="white")
        
        # Required settings
        for key in ['course', 'assignment']:
            value = cfg.get(key)
            if value is not None:
                table.add_row("Required", key, f"[{colors['success']}]{value}[/{colors['success']}]")
            else:
                table.add_row("Required", key, f"[{colors['error']}]NOT SET[/{colors['error']}]")
        
        # Submission settings  
        submission_defaults = {
            'zip_name': 'submission.zip',
            'bundle': ['*']
        }
        for key in ['zip_name', 'bundle']:
            value = cfg.get(key, submission_defaults[key])
            table.add_row("Submission", key, str(value))
        
        # Behavior settings
        behavior_defaults = {
            'notify_when_graded': True,
            'headless': False
        }
        for key in ['notify_when_graded', 'headless']:
            value = cfg.get(key, behavior_defaults[key])
            table.add_row("Behavior", key, str(value))
            
        # Security settings
        security_defaults = {
            'always_fresh_login': False,
            'manual_login': False,
            'no_session_save': False
        }
        for key in ['always_fresh_login', 'manual_login', 'no_session_save']:
            value = cfg.get(key, security_defaults[key])
            table.add_row("Security", key, str(value))
        
        # Check credentials
        username = os.getenv('GRADESCOPE_USERNAME')
        password = os.getenv('GRADESCOPE_PASSWORD')
        
        if username:
            table.add_row("Credentials", "Username", f"[{colors['success']}]{username}[/{colors['success']}]")
        else:
            table.add_row("Credentials", "Username", f"[{colors['error']}]NOT SET[/{colors['error']}]")
        
        if password:
            table.add_row("Credentials", "Password", f"[{colors['success']}]{'*' * len(password)}[/{colors['success']}]")
        else:
            table.add_row("Credentials", "Password", f"[{colors['error']}]NOT SET[/{colors['error']}]")
        
        console.print(table)
        
        # Show credential help
        if not username or not password:
            help_panel = Panel(
                f"To set credentials: [{colors['primary']}]gradescope credentials[/{colors['primary']}] or set environment variables",
                title="Setup Help",
                border_style=colors['primary'],
                box=box.ROUNDED
            )
            console.print(help_panel)
                
    except Exception as e:
        log_error(f"Configuration error: {e}")
        return 1


@cli.command()
def debug_session():
    """Debug session persistence status."""
    from .core import SessionManager
    import asyncio
    
    async def check_session():
        session_manager = SessionManager()
        context, playwright, browser = await session_manager.get_browser_context(False)  # Non-headless for debugging
        
        try:
            # Check what's in the session directory
            click.echo(f"Session directory: {session_manager.session_dir}")
            click.echo(f"Session exists: {session_manager.session_dir.exists()}")
            
            if session_manager.session_dir.exists():
                import os
                session_files = []
                for root, dirs, files in os.walk(session_manager.session_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), session_manager.session_dir)
                        session_files.append(rel_path)
                click.echo(f"Session files: {session_files[:10]}...")  # Show first 10 files
            
            is_logged_in = await session_manager.is_logged_in(context)
            click.echo(f"Logged in: {is_logged_in}")
            
            # Check session status
            page = await context.new_page()
            cookies = await context.cookies()
            
            gradescope_cookies = [c for c in cookies if 'gradescope' in c.get('domain', '')]
            qut_cookies = [c for c in cookies if 'qut.edu.au' in c.get('domain', '') or 'esoe.qut.edu.au' in c.get('domain', '')]
            
            click.echo(f"📊 Session Status:")
            click.echo(f"   Gradescope cookies: {len(gradescope_cookies)}")
            click.echo(f"   QUT SSO cookies: {len(qut_cookies)}")
            
            if qut_cookies:
                click.echo("✅ QUT SSO session active")
            else:
                click.echo("❌ No QUT SSO session - explains why login required")
            
            # Test cookie persistence
            try:
                await context.add_cookies([{
                    'name': 'test_persistence',
                    'value': 'working',
                    'domain': '.gradescope.com.au',
                    'path': '/'
                }])
                
                test_cookies = await context.cookies('https://gradescope.com.au')
                test_cookie = next((c for c in test_cookies if c['name'] == 'test_persistence'), None)
                if test_cookie:
                    click.echo("✅ Cookie persistence working")
                else:
                    click.echo("❌ Cookie persistence failed")
            except Exception as e:
                click.echo(f"❌ Cookie test failed: {e}")
            
            await page.close()
        finally:
            if browser:
                await browser.close()
            else:
                await context.close()
            await playwright.stop()
    
    asyncio.run(check_session())

@cli.command()
def cleanup():
    """Clear saved session data."""
    from .core import SessionManager
    session_manager = SessionManager()
    session_manager.cleanup_session()
    click.echo("✅ Session data cleared\n")


@cli.command()
def ui():
    """Customize the UI experience and themes."""
    from .ui_config import (get_available_colors, get_current_colors, set_color, get_color_categories,
                           load_ui_config, update_setting, reset_to_defaults, get_config_path, reset_colors_to_default)
    from .rich_console import reload_ui_config, create_ui_config_panel
    
    def show_current_config():
        """Show current UI configuration."""
        config = load_ui_config()
        
        import os
        os.system('cls' if os.name == 'nt' else 'clear')  # More aggressive clear
        config_panel = create_ui_config_panel(config)
        console.print(config_panel)
        console.print(f"\n[dim]Config file:[/dim] {get_config_path()}")
        
    def customize_colors():
        """Customize UI colors."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')  # More aggressive clear
        colors = get_colors()
        console.print(f"[bold {colors['primary']}]Customize Colors[/bold {colors['primary']}]\n")
        
        categories = get_color_categories()
        current_colors = get_current_colors()
        # Build reverse map from rich code -> friendly name
        available_map = get_available_colors()
        reverse_color_map = {v: k for k, v in available_map.items()}
        
        for i, category in enumerate(categories, 1):
            current_color = current_colors.get(category, 'cyan')
            friendly_name = reverse_color_map.get(current_color, current_color)
            console.print(f"[{colors['primary']}][{i}][/{colors['primary']}] [bold]{category.title()}[/bold]: [{current_color}]■[/{current_color}] {friendly_name}")
        
        console.print(f"[{colors['primary']}][{len(categories) + 1}][/{colors['primary']}] Reset to defaults")
        console.print(f"[{colors['primary']}][{len(categories) + 2}][/{colors['primary']}] Back to menu")
        
        try:
            choice = Prompt.ask(f"Choose color to change [{colors['primary']}][1-{len(categories) + 2}][/{colors['primary']}]", choices=[str(i) for i in range(1, len(categories) + 3)], show_choices=False)
            choice_idx = int(choice) - 1
            
            if choice_idx < len(categories):
                # User wants to change a specific color
                category = categories[choice_idx]
                change_specific_color(category)
            elif choice_idx == len(categories):
                # Reset to defaults
                if reset_colors_to_default():
                    reload_ui_config()
                    log_success("Colors reset to defaults")
                else:
                    log_error("Failed to reset colors")
            # else: Back to menu (do nothing)
        except (ValueError, KeyboardInterrupt):
            pass
    
    def change_specific_color(category: str):
        """Change a specific color category."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')  # More aggressive clear
        colors = get_colors()
        console.print(f"[bold {colors['primary']}]Choose {category.title()} Color[/bold {colors['primary']}]\n")
        
        available_colors = get_available_colors()
        current_color = get_current_colors().get(category, 'cyan')
        
        # Display color options in a nice grid
        colors_list = list(available_colors.items())
        for i, (name, value) in enumerate(colors_list, 1):
            marker = f" [{colors['success']}](current)[/{colors['success']}]" if value == current_color else ""
            console.print(f"[{colors['primary']}][{i:02}][/{colors['primary']}] [{value}]■[/{value}] {name.title()}{marker}")
            if i % 3 == 0:  # New line every 3 colors
                console.print()
        
        console.print(f"[{colors['primary']}][{len(colors_list) + 1}][/{colors['primary']}] Back to color menu")
        
        try:
            colors = get_colors()
            choice = Prompt.ask(f"Choose color [{colors['primary']}][1-{len(colors_list) + 1}][/{colors['primary']}]", choices=[str(i) for i in range(1, len(colors_list) + 2)], show_choices=False)
            choice_idx = int(choice) - 1
            
            if choice_idx < len(colors_list):
                color_name, color_value = colors_list[choice_idx]
                if set_color(category, color_value):
                    reload_ui_config()
                    log_success(f"{category.title()} color changed to {color_name}")
                else:
                    log_error("Failed to set color")
            # else: Back to color menu (do nothing)
        except (ValueError, KeyboardInterrupt):
            pass
        
    
    def toggle_setting():
        """Toggle various UI settings."""
        config = load_ui_config()
        
        import os
        os.system('cls' if os.name == 'nt' else 'clear')  # More aggressive clear
        colors = get_colors()
        console.print(f"[bold {colors['primary']}]UI Settings[/bold {colors['primary']}]\n")
        
        settings = [
            ("log_timestamps", "Timestamps", config['log_timestamps']),
            ("animations", "Animations", config['animations']),
            ("compact_mode", "Compact Mode", config['compact_mode']),
            ("show_step_timings", "Step Timings", config['show_step_timings'])
        ]
        
        for i, (key, name, value) in enumerate(settings, 1):
            status = "On" if value else "Off"
            console.print(f"[{colors['primary']}][{i}][/{colors['primary']}] {name}: {status}")
        
        console.print(f"[{colors['primary']}][{len(settings) + 1}][/{colors['primary']}] Back to menu")
        
        try:
            colors = get_colors()
            choice = Prompt.ask(f"Toggle setting [{colors['primary']}][1-{len(settings) + 1}][/{colors['primary']}]", choices=[str(i) for i in range(1, len(settings) + 2)], show_choices=False)
            choice_idx = int(choice) - 1
            
            if choice_idx < len(settings):
                key, name, current_value = settings[choice_idx]
                new_value = not current_value
                update_setting(key, new_value)
                reload_ui_config()
                status = "enabled" if new_value else "disabled"
                log_success(f"{name} {status}")
        except (ValueError, KeyboardInterrupt):
            pass
        
    
    # Main UI customization loop
    while True:
        try:
            show_current_config()
            
            colors = get_colors()
            console.print(f"\n[bold]Options:[/bold]")
            console.print(f"[{colors['primary']}][1][/{colors['primary']}] Customize colors")
            console.print(f"[{colors['primary']}][2][/{colors['primary']}] Toggle settings")
            console.print(f"[{colors['primary']}][3][/{colors['primary']}] Reset to defaults")
            console.print(f"[{colors['primary']}][4][/{colors['primary']}] Exit")
            
            choice = Prompt.ask(f"Choose [{colors['primary']}][1/2/3/4][/{colors['primary']}]", choices=["1", "2", "3", "4"], show_choices=False)
            
            if choice == "1":
                customize_colors()
            elif choice == "2":
                toggle_setting()
            elif choice == "3":
                reset_to_defaults()
                reload_ui_config()
                log_success("UI configuration reset to defaults")
            elif choice == "4":
                console.print("[dim]Goodbye![/dim]")
                break
                
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            break


@cli.command()
def credentials():
    """Manage credentials - view, set, or clear them."""
    import os
    
    def get_credential_data():
        """Get current credential status."""
        user_env = _user_env_path()
        username = os.getenv('GRADESCOPE_USERNAME')
        password = os.getenv('GRADESCOPE_PASSWORD')
        env_path = str(user_env) if user_env.exists() else None
        return username, password, env_path, user_env
    
    def handle_saved_credentials():
        """Handle saved credentials actions."""
        username, password, env_path, user_env = get_credential_data()
        
        submenu = create_submenu_panel(
            "💾 Saved Credentials (.env)",
            ["Save/update credentials", "Delete saved credentials"],
            "Back to main menu"
        )
        
        console.print(submenu)
        colors = get_colors()
        choice = Prompt.ask(f"❯ Choose [{colors['primary']}][1/2/3][/{colors['primary']}]", choices=["1", "2", "3"], show_choices=False)
        
        if choice == "1":
            colors = get_colors()
            console.print(f"\n[{colors['primary']}]Setting up credentials...[/{colors['primary']}]")
            try:
                from .credentials import get_credentials
                # Save/update credentials to user-level .env
                creds = get_credentials(set_session_vars=False, persist_to_env=True, force_prompt=True)
                # Reload user-level .env into current process so UI reflects immediately
                user_env_path = _user_env_path()
                if user_env_path.exists():
                    load_dotenv(dotenv_path=user_env_path, override=True)
                # Also set directly into this process for immediate reflection
                if isinstance(creds, tuple) and len(creds) == 2:
                    os.environ['GRADESCOPE_USERNAME'] = creds[0]
                    os.environ['GRADESCOPE_PASSWORD'] = creds[1]
                log_success("Saved credentials to user-level .env")
                Prompt.ask("\nPress Enter to continue", default="")
            except Exception as e:
                log_error(f"Error: {e}")
                Prompt.ask("\nPress Enter to continue", default="")
            
        elif choice == "2":
            try:
                if user_env.exists():
                    user_env.unlink()
                    # Clear from current session so UI reflects immediately
                    os.environ.pop('GRADESCOPE_USERNAME', None)
                    os.environ.pop('GRADESCOPE_PASSWORD', None)
                    log_success(f"Deleted: {user_env}")
                    Prompt.ask("\nPress Enter to continue", default="")
                else:
                    log_warning(f"No credentials file found")
            except Exception as e:
                log_error(f"Failed to delete: {e}")
                Prompt.ask("\nPress Enter to continue", default="")
            # choice == "3" falls through to return
    
    def handle_env_vars():
        """Handle environment variables submenu."""
        while True:
            try:
                import os
                os.system('cls' if os.name == 'nt' else 'clear')  # More aggressive clear
                
                submenu = create_submenu_panel(
                    "🌍 Environment Variables",
                    ["How to set environment variables", "How to delete environment variables", "View current variables"],
                    "Back to main menu"
                )
                
                console.print(submenu)
                colors = get_colors()
                choice = Prompt.ask(f"❯ Choose [{colors['primary']}][1/2/3/4][/{colors['primary']}]", choices=["1", "2", "3", "4"], show_choices=False)
                
                if choice == "1":
                    show_set_env_commands()
                elif choice == "2":
                    show_delete_env_commands()
                elif choice == "3":
                    show_current_env_vars()
                elif choice == "4":
                    break  # Back to main menu
                    
            except KeyboardInterrupt:
                break
    
    def show_set_env_commands():
        """Show commands to set environment variables."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        colors = get_colors()
        
        help_panel = create_submenu_panel(
            "📝 Setting Environment Variables",
            [
                "Windows PowerShell: $env:GRADESCOPE_USERNAME='n12345678'; $env:GRADESCOPE_PASSWORD='your_password'",
                "Linux/Mac: export GRADESCOPE_USERNAME='n12345678'; export GRADESCOPE_PASSWORD='your_password'"
            ],
            "Back to environment menu"
        )
        
        console.print(help_panel)
        console.print(f"\n[{colors['warning']}]💡 Note:[/{colors['warning']}] These are session-only (temporary)")
        console.print(f"[dim]For permanent storage, use option 1 in the main menu (.env files)[/dim]")
        
        Prompt.ask("\nPress Enter to continue", default="")
    
    def show_delete_env_commands():
        """Show commands to delete environment variables."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        colors = get_colors()
        
        help_panel = create_submenu_panel(
            "🗑️  Deleting Environment Variables",
            [
                "Windows PowerShell: Remove-Item Env:GRADESCOPE_USERNAME; Remove-Item Env:GRADESCOPE_PASSWORD",
                "Windows PowerShell (alt): $env:GRADESCOPE_USERNAME=$null; $env:GRADESCOPE_PASSWORD=$null",
                "Linux/Mac: unset GRADESCOPE_USERNAME; unset GRADESCOPE_PASSWORD"
            ],
            "Back to environment menu"
        )
        
        console.print(help_panel)
        console.print(f"\n[{colors['warning']}]⚠️ Warning:[/{colors['warning']}] This will clear credentials for current session")
        console.print(f"[dim]To delete .env files, use option 1 > 2 in the main menu[/dim]")
        
        Prompt.ask("\nPress Enter to continue", default="")
    
    def show_current_env_vars():
        """Show current environment variable status."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        colors = get_colors()
        
        username = os.getenv('GRADESCOPE_USERNAME')
        password = os.getenv('GRADESCOPE_PASSWORD')
        
        console.print(f"[bold {colors['primary']}]Current Environment Variables[/bold {colors['primary']}]\n")
        
        if username:
            console.print(f"[{colors['success']}]✓[/{colors['success']}] GRADESCOPE_USERNAME: [{colors['primary']}]{username}[/{colors['primary']}]")
        else:
            console.print(f"[{colors['error']}]✗[/{colors['error']}] GRADESCOPE_USERNAME: [dim]Not set[/dim]")
        
        if password:
            masked = "•" * min(len(password), 12)
            console.print(f"[{colors['success']}]✓[/{colors['success']}] GRADESCOPE_PASSWORD: [{colors['primary']}]{masked}[/{colors['primary']}]")
        else:
            console.print(f"[{colors['error']}]✗[/{colors['error']}] GRADESCOPE_PASSWORD: [dim]Not set[/dim]")
        
        console.print(f"\n[dim]These are session-only variables (temporary)[/dim]")
        
        Prompt.ask("\nPress Enter to continue", default="")
    
    # Main interface loop
    while True:
        try:
            username, password, env_path, user_env = get_credential_data()
            interface = create_credentials_interface(username, password, env_path)
            
            console.clear()
            console.print(interface)
            colors = get_colors()
            choice = Prompt.ask(f"❯ Choose [{colors['primary']}][1/2/3][/{colors['primary']}]", choices=["1", "2", "3"], show_choices=False)
            
            if choice == "1":
                handle_saved_credentials()
            elif choice == "2":
                handle_env_vars()
            elif choice == "3":
                console.print("[dim]👋 Goodbye![/dim]")
                break
                    
        except KeyboardInterrupt:
            console.print("\n[dim]👋 Goodbye![/dim]")
            break
        except Exception as e:
            log_error(f"Error: {e}")
            break


@cli.command()
def hooks():
    """Set up Git hooks for automated submissions."""
    from pathlib import Path
    import stat
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        log_error("Not in a Git repository. Please run this command from the root of a Git repository.")
        return
    
    hooks_dir = Path('.git/hooks')
    hooks_dir.mkdir(exist_ok=True)
    
    colors = get_colors()
    
    def show_hooks_menu():
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        console.print(f"[bold {colors['primary']}]Git Hooks Setup[/bold {colors['primary']}]\n")
        
        # Check existing hooks
        pre_commit_exists = (hooks_dir / 'pre-commit').exists()
        post_commit_exists = (hooks_dir / 'post-commit').exists()
        
        console.print("[bold]Available Git Hooks:[/bold]")
        console.print(f"[{colors['primary']}]1[/{colors['primary']}] Install pre-commit hook (submit + wait for grade) {'[' + colors['success'] + ']✓ Installed[/' + colors['success'] + ']' if pre_commit_exists else ''}")
        console.print(f"[{colors['primary']}]2[/{colors['primary']}] Install post-commit hook (submit + wait for grade) {'[' + colors['success'] + ']✓ Installed[/' + colors['success'] + ']' if post_commit_exists else ''}")
        console.print(f"[{colors['primary']}]3[/{colors['primary']}] Install quick hooks (submit only, no grade wait)")
        console.print(f"[{colors['primary']}]4[/{colors['primary']}] View current hooks")
        console.print(f"[{colors['primary']}]5[/{colors['primary']}] Remove hooks")
        console.print(f"[{colors['primary']}]6[/{colors['primary']}] Exit")
        
        return pre_commit_exists, post_commit_exists
    
    def create_pre_commit_hook():
        hook_content = '''#!/bin/bash
# Pre-commit hook for Gradescope submissions
echo "Pre-commit: Checking for gradescope.yml..."

if [ -f "gradescope.yml" ]; then
    echo "Found gradescope.yml, running submission with grade monitoring..."
    gradescope submit --headless
    if [ $? -eq 0 ]; then
        echo "Gradescope submission and grading completed successfully"
    else
        echo "Gradescope submission failed"
        echo "Commit will proceed anyway..."
    fi
else
    echo "No gradescope.yml found, skipping submission"
fi
'''
        hook_file = hooks_dir / 'pre-commit'
        hook_file.write_text(hook_content, encoding='utf-8')
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        log_success("Pre-commit hook installed successfully")
    
    def create_post_commit_hook():
        hook_content = '''#!/bin/bash
# Post-commit hook for Gradescope submissions
echo "Post-commit: Checking for gradescope.yml..."

if [ -f "gradescope.yml" ]; then
    echo "Found gradescope.yml, running submission with grade monitoring..."
    gradescope submit --headless
    if [ $? -eq 0 ]; then
        echo "Gradescope submission and grading completed successfully"
    else
        echo "Gradescope submission failed"
    fi
else
    echo "No gradescope.yml found, skipping submission"
fi
'''
        hook_file = hooks_dir / 'post-commit'
        hook_file.write_text(hook_content, encoding='utf-8')
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        log_success("Post-commit hook installed successfully")
    
    def create_quick_pre_commit_hook():
        hook_content = '''#!/bin/bash
# Pre-commit hook for Gradescope submissions (quick mode)
echo "Pre-commit: Checking for gradescope.yml..."

if [ -f "gradescope.yml" ]; then
    echo "Found gradescope.yml, running quick submission..."
    gradescope submit --headless --no-grade-wait
    if [ $? -eq 0 ]; then
        echo "Gradescope submission successful (not waiting for grade)"
    else
        echo "Gradescope submission failed"
        echo "Commit will proceed anyway..."
    fi
else
    echo "No gradescope.yml found, skipping submission"
fi
'''
        hook_file = hooks_dir / 'pre-commit'
        hook_file.write_text(hook_content, encoding='utf-8')
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        log_success("Quick pre-commit hook installed successfully")
    
    def create_quick_post_commit_hook():
        hook_content = '''#!/bin/bash
# Post-commit hook for Gradescope submissions (quick mode)
echo "Post-commit: Checking for gradescope.yml..."

if [ -f "gradescope.yml" ]; then
    echo "Found gradescope.yml, running quick submission..."
    gradescope submit --headless --no-grade-wait
    if [ $? -eq 0 ]; then
        echo "Gradescope submission successful (not waiting for grade)"
    else
        echo "Gradescope submission failed"
    fi
else
    echo "No gradescope.yml found, skipping submission"
fi
'''
        hook_file = hooks_dir / 'post-commit'
        hook_file.write_text(hook_content, encoding='utf-8')
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)
        log_success("Quick post-commit hook installed successfully")
    
    def setup_quick_hooks():
        """Set up quick hooks submenu."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        console.print(f"[bold {colors['primary']}]Quick Git Hooks Setup[/bold {colors['primary']}]\n")
        console.print("[dim]Quick hooks submit to Gradescope but don't wait for grades[/dim]\n")
        
        console.print(f"[{colors['primary']}][1][/{colors['primary']}] Install quick pre-commit hook")
        console.print(f"[{colors['primary']}][2][/{colors['primary']}] Install quick post-commit hook") 
        console.print(f"[{colors['primary']}][3][/{colors['primary']}] Install both quick hooks")
        console.print(f"[{colors['primary']}][4][/{colors['primary']}] Back to main menu")
        
        try:
            colors = get_colors()
            choice = Prompt.ask(f"Choose option [{colors['primary']}][1/2/3/4][/{colors['primary']}]", choices=["1", "2", "3", "4"], show_choices=False)
            
            if choice == "1":
                create_quick_pre_commit_hook()
            elif choice == "2":
                create_quick_post_commit_hook()
            elif choice == "3":
                create_quick_pre_commit_hook()
                create_quick_post_commit_hook()
            # choice == "4" falls through to return
        except (ValueError, KeyboardInterrupt):
            pass
    
    def view_hooks():
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        console.print(f"[bold {colors['primary']}]Current Git Hooks[/bold {colors['primary']}]\n")
        
        for hook_name in ['pre-commit', 'post-commit']:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                console.print(f"[{colors['success']}]✓[/{colors['success']}] {hook_name}")
                try:
                    content = hook_file.read_text(encoding='utf-8')
                    if 'gradescope' in content.lower() or 'gradescope submit' in content.lower():
                        console.print(f"  [{colors['primary']}]→[/{colors['primary']}] Contains Gradescope automation")
                    else:
                        console.print(f"  [{colors['warning']}]→[/{colors['warning']}] Custom hook (not Gradescope)")
                except:
                    console.print(f"  [{colors['error']}]→[/{colors['error']}] Cannot read hook")
            else:
                console.print(f"[{colors['error']}]✗[/{colors['error']}] {hook_name} (not installed)")
        
        Prompt.ask("\nPress Enter to continue", default="")
    
    def remove_hooks():
        removed = 0
        for hook_name in ['pre-commit', 'post-commit']:
            hook_file = hooks_dir / hook_name
            if hook_file.exists():
                try:
                    content = hook_file.read_text(encoding='utf-8')
                    # Look for multiple identifying strings to catch our hooks
                    if ('gradescope' in content.lower() or 
                        'gradescope submit' in content.lower() or
                        'Gradescope submissions' in content):
                        hook_file.unlink()
                        log_success(f"Removed {hook_name} hook")
                        removed += 1
                    else:
                        log_warning(f"Skipped {hook_name} (not a Gradescope hook)")
                except:
                    log_error(f"Failed to process {hook_name}")
        
        if removed == 0:
            log_warning("No Gradescope hooks found to remove")
        else:
            log_success(f"Removed {removed} Gradescope hook(s)")
    
    # Main menu loop
    while True:
        try:
            pre_commit_exists, post_commit_exists = show_hooks_menu()
            
            colors = get_colors()
            choice = Prompt.ask(f"Choose an option [{colors['primary']}][1/2/3/4/5/6][/{colors['primary']}]", choices=["1", "2", "3", "4", "5", "6"], show_choices=False)
            
            if choice == "1":
                if pre_commit_exists:
                    if Prompt.ask(f"Pre-commit hook already exists. Overwrite? [{colors['primary']}][y/n][/{colors['primary']}]", choices=["y", "n"], default="n", show_choices=False) == "y":
                        create_pre_commit_hook()
                else:
                    create_pre_commit_hook()
            elif choice == "2":
                if post_commit_exists:
                    if Prompt.ask(f"Post-commit hook already exists. Overwrite? [{colors['primary']}][y/n][/{colors['primary']}]", choices=["y", "n"], default="n", show_choices=False) == "y":
                        create_post_commit_hook()
                else:
                    create_post_commit_hook()
            elif choice == "3":
                setup_quick_hooks()
            elif choice == "4":
                view_hooks()
            elif choice == "5":
                remove_hooks()
                Prompt.ask("\nPress Enter to continue", default="")
            elif choice == "6":
                console.print("[dim]Git hooks setup complete![/dim]")
                break
                
        except KeyboardInterrupt:
            console.print("\n[dim]Git hooks setup cancelled[/dim]")
            break


@cli.command()
def doctor():
    """Check system requirements and configuration."""
    console.clear()
    colors = get_colors()
    console.print(f"[bold {colors['primary']}]System Diagnostics[/bold {colors['primary']}]\n")

    checks = []
    from rich.status import Status
    status = console.status("[dim]Running system checks...[/dim]", spinner="dots")
    status.start()
    
    # Check Python version
    import sys
    if sys.version_info >= (3, 8):
        checks.append({
            "component": "Python", 
            "status": "ok", 
            "details": sys.version.split()[0]
        })
    else:
        checks.append({
            "component": "Python", 
            "status": "error", 
            "details": f"{sys.version.split()[0]} (requires 3.8+)"
        })
    
    # Check dependencies
    try:
        import playwright
        # Try to get version from multiple sources
        playwright_version = None
        try:
            # Method 1: Try __version__ attribute
            from playwright import __version__ as playwright_version
        except ImportError:
            try:
                # Method 2: Try importlib.metadata (Python 3.8+)
                import importlib.metadata
                playwright_version = importlib.metadata.version('playwright')
            except (ImportError, Exception):
                try:
                    # Method 3: Try pkg_resources (fallback)
                    import pkg_resources
                    playwright_version = pkg_resources.get_distribution('playwright').version
                except Exception:
                    pass
        
        if playwright_version:
            checks.append({
                "component": "Playwright", 
                "status": "ok", 
                "details": f"v{playwright_version}"
            })
        else:
            checks.append({
                "component": "Playwright", 
                "status": "ok", 
                "details": "Installed (version unknown)"
            })
    except ImportError:
        checks.append({
            "component": "Playwright", 
            "status": "error", 
            "details": "Not installed"
        })
    
    try:
        import yaml
        checks.append({
            "component": "PyYAML", 
            "status": "ok", 
            "details": "Available"
        })
    except ImportError:
        checks.append({
            "component": "PyYAML", 
            "status": "error", 
            "details": "Not installed"
        })
    
    # Check Playwright browser installation (fast file check)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Check if Chromium executable exists without launching
            chromium_path = p.chromium.executable_path
            if chromium_path and Path(chromium_path).exists():
                checks.append({
                    "component": "Chromium Browser", 
                    "status": "ok", 
                    "details": "Available"
                })
            else:
                checks.append({
                    "component": "Chromium Browser", 
                    "status": "error", 
                    "details": "Run 'playwright install chromium'"
                })
    except ImportError:
        checks.append({
            "component": "Chromium Browser", 
            "status": "error", 
            "details": "Playwright not available"
        })
    except Exception as e:
        checks.append({
            "component": "Chromium Browser", 
            "status": "error", 
            "details": "Run 'playwright install chromium'"
        })
    
    # Check for config files
    cfg = Config()
    config_file = cfg._find_config_file()
    if config_file:
        try:
            cfg.validate()
            checks.append({
                "component": "Configuration", 
                "status": "ok", 
                "details": f"Valid: {Path(config_file).name}"
            })
        except Exception as e:
            checks.append({
                "component": "Configuration", 
                "status": "warning", 
                "details": f"Invalid: {e}"
            })
    else:
        checks.append({
            "component": "Configuration", 
            "status": "warning", 
            "details": "Run 'gradescope init'"
        })
    
    # Check credentials
    username = os.getenv('GRADESCOPE_USERNAME')
    password = os.getenv('GRADESCOPE_PASSWORD')
    
    if username and password:
        checks.append({
            "component": "Credentials", 
            "status": "ok", 
            "details": "Both username and password set"
        })
    elif username or password:
        checks.append({
            "component": "Credentials", 
            "status": "warning", 
            "details": "Incomplete (missing username or password)"
        })
    else:
        checks.append({
            "component": "Credentials", 
            "status": "warning", 
            "details": "Run 'gradescope credentials'"
        })
    
    # Create and display table
    from .rich_console import create_doctor_table
    table = create_doctor_table(checks)
    status.stop()
    console.print(table)
    
    # Count issues
    errors = sum(1 for check in checks if check["status"] == "error")
    warnings = sum(1 for check in checks if check["status"] == "warning")
    
    # Summary and quick actions
    if errors == 0 and warnings == 0:
        console.print(f"\n[bold {colors['success']}]🎉 All systems ready![/bold {colors['success']}]")
    elif errors == 0:
        console.print(f"\n[{colors['warning']}]⚠️ {warnings} warning(s) - core functionality available[/{colors['warning']}]")
    else:
        console.print(f"\n[{colors['error']}]❌ {errors} error(s), {warnings} warning(s) - fix errors first[/{colors['error']}]")
        console.print(f"[dim]Quick fixes: [{colors['success']}]gradescope credentials[/{colors['success']}] • [{colors['success']}]gradescope init[/{colors['success']}] • [{colors['success']}]playwright install chromium[/{colors['success']}][/dim]")
    
    console.print()


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
