#!/usr/bin/env python3
"""
Leme DevOps CLI - Main entry point
Tool for automatic DevOps environment configuration
"""

import typer
from rich import print
from typing import Optional

from .commands.install_commands import (
    install_docker, uninstall_docker, check_docker_status, 
    system_info, install_terraform, install_azure_cli, install_aws_cli
)
from .commands.environment_commands import setup_environment, environment_status

# --- Application Configuration ---
app = typer.Typer(
    name="leme",
    help="Leme DevOps CLI - Automatic DevOps environment configuration",
    add_completion=False,
    rich_markup_mode="rich"
)

# --- Main Callback for Global Options ---
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, 
        "--version", 
        "-v",
        help="Show version and exit",
        is_eager=True
    ),
    help: Optional[bool] = typer.Option(
        None,
        "--help",
        "-h",
        is_eager=True,
        help="Show this help message and exit.",
        show_default=False
    )
):
    """
    Leme DevOps CLI - Automate your development environment setup!
    
    This tool automatically installs and configures all tools 
    required for DevOps development, including:
    
    • Docker - Containerization platform
    • Git - Version control system
    • Terraform - Infrastructure as code
    • Azure CLI - Azure interface
    • AWS CLI - AWS interface
    • kubectl - Kubernetes client
    • Ansible - Automation and configuration
    • watch - Periodic command execution
    
    Use 'leme --help' to see all available commands.
    """
    if version:
        print("[bold blue]Leme DevOps CLI[/bold blue] [green]v1.0.0[/green]")
        print("Tool for automatic DevOps environment configuration")
        raise typer.Exit()
        
    if help:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    
    if ctx.invoked_subcommand is None:
        print("[bold blue]Leme DevOps CLI[/bold blue] - Welcome!")
        print()
        print("To get started, use one of the main commands:")
        print("  • [cyan]leme setup[/cyan] - Configure complete environment")
        print("  • [cyan]leme status[/cyan] - View tools status")
        print("  • [cyan]leme install --help[/cyan] - View installation options")
        print()
        print("Use [cyan]leme --help[/cyan] to see all commands.")
        raise typer.Exit()


# --- Sub-application for installation ---
install_app = typer.Typer(
    name="install",
    help="Install specific DevOps environment tools",
    rich_markup_mode="rich"
)
app.add_typer(install_app, name="install")


# --- Installation Commands ---

@install_app.command("docker")
def install_docker_command(
    check_only: bool = typer.Option(False, "--check-only", help="Only check if Docker is installed"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
    manual: bool = typer.Option(False, "--manual", help="Show manual installation instructions"),
    no_test: bool = typer.Option(False, "--no-test", help="Do not test installation after completion")
):
    """Install Docker automatically based on operating system."""
    install_docker(check_only, force, manual, no_test)


@install_app.command("azure")
def install_azure_cli_command(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
    manual: bool = typer.Option(False, "--manual", help="Show manual installation instructions")
):
    """Install Azure CLI automatically based on operating system."""
    install_azure_cli(force, manual)


@install_app.command("terraform")
def install_terraform_command(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
    manual: bool = typer.Option(False, "--manual", help="Show manual installation instructions")
):
    """Install Terraform automatically based on operating system."""
    install_terraform(force, manual)


@install_app.command("aws")
def install_aws_cli_command(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
    manual: bool = typer.Option(False, "--manual", help="Show manual installation instructions")
):
    """Install AWS CLI v2 automatically based on operating system."""
    install_aws_cli(force, manual)


# --- Main Commands ---

@app.command("setup")
def setup_command(
    check_only: bool = typer.Option(False, "--check-only", help="Only check current environment"),
    required_only: bool = typer.Option(False, "--required-only", help="Install only required tools"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker installation"),
    force: bool = typer.Option(False, "--force", "-f", help="Force tool reinstallation"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode (LEGACY - now default)"),
    tools: Optional[str] = typer.Option(None, "--tools", "-t", help="Install only specific tools (e.g: git,docker)")
):
    """Configure complete DevOps environment for the course."""
    tools_list = tools.split(',') if tools else None
    setup_environment(check_only, required_only, skip_docker, force, interactive, tools_list)


@app.command("status")
def status_command():
    """Show detailed status of all DevOps tools."""
    environment_status()


@app.command("info")
def info_command():
    """Show detailed operating system information."""
    system_info()


# --- Maintenance Commands ---

@app.command("uninstall-docker", hidden=True)
def uninstall_docker_command():
    """Remove Docker from system."""
    uninstall_docker()


# --- Aliases for common commands ---
@app.command("check", hidden=True)
def check_command():
    """Alias for 'leme status'"""
    environment_status()


def cli_main():
    """Entry point for leme command installed via pip"""
    app()


if __name__ == "__main__":
    cli_main()