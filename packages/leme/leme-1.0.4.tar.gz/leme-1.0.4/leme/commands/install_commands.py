"""Commands for tool installation."""

import typer
from rich import print
from typing import Optional

from ..system.docker_installer import DockerInstaller
from ..system.installers.terraform_installer import TerraformInstaller
from ..system.installers.azure_cli_installer import AzureCliInstaller
from ..system.installers.aws_cli_installer import AwsCliInstaller
from ..system.system_detector import SystemDetector


def install_docker(
    check_only: bool = typer.Option(False, "--check-only", help="Only check if Docker is installed"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if already installed"),
    manual: bool = typer.Option(False, "--manual", help="Show manual installation instructions"),
    no_test: bool = typer.Option(False, "--no-test", help="Do not test installation after completion")
) -> None:
    """
    Install Docker automatically based on detected operating system.
    
    Supported systems:
    - Ubuntu/Debian (including WSL)
    - macOS (Intel and Apple Silicon)
    - CentOS/RHEL/Fedora
    """
    try:
        docker_installer = DockerInstaller()
        
        # Check-only mode
        if check_only:
            print("[bold blue]Checking Docker installation...[/bold blue]")
            print()
            docker_installer.print_status()
            return
        
        # Manual instructions mode
        if manual:
            print("[bold blue]Manual installation instructions[/bold blue]")
            print()
            docker_installer.get_manual_instructions()
            return
        
        # Automatic installation
        success = docker_installer.install(
            force=force, 
            test_after_install=not no_test
        )
        
        if success:
            print()
            print("[bold green]Installation completed![/bold green]")
            print()
            print("[bold]Next steps:[/bold]")
            print("• Use 'docker --version' to verify installation")
            print("• Use 'docker run hello-world' to test")
            if docker_installer.system_info.os_type.value != "macos":
                print("• Logout/login to apply group permissions")
        else:
            raise typer.Exit(code=1)
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def uninstall_docker() -> None:
    """
    Remove Docker from system.
    """
    try:
        docker_installer = DockerInstaller()
        
        print("[bold yellow]Docker Removal[/bold yellow]")
        print(f"System: {docker_installer.system_info}")
        print()
        
        success = docker_installer.uninstall()
        
        if success:
            print()
            print("[bold green]Docker removed successfully![/bold green]")
        else:
            raise typer.Exit(code=1)
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def check_docker_status() -> None:
    """
    Check Docker installation status.
    """
    try:
        docker_installer = DockerInstaller()
        
        print("[bold blue]Docker Status[/bold blue]")
        print()
        docker_installer.print_status()
        
        # Additional information
        info = docker_installer.check_installation()
        print()
        
        if info['installed'] and info['working']:
            print("[bold green]✓ Docker is ready to use![/bold green]")
        elif info['installed'] and not info['working']:
            print("[bold yellow]⚠ Docker installed but not working[/bold yellow]")
            print("Try:")
            print("• Restart the system")
            print("• Start Docker manually")
            if docker_installer.system_info.os_type.value == "macos":
                print("• Open Docker Desktop")
        elif info['supported']:
            print("[bold red]✗ Docker is not installed[/bold red]")
            print(f"Use: [cyan]python3 main.py install docker[/cyan]")
        else:
            print("[bold red]✗ System not supported[/bold red]")
            print("Visit: https://docs.docker.com/get-docker/")
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def system_info() -> None:
    """
    Show detailed system information.
    """
    try:
        from ..system.system_detector import SystemDetector
        
        system_info = SystemDetector.detect()
        
        print("[bold blue]System Information[/bold blue]")
        print()
        print(f"[bold]Operating System:[/bold] {system_info.os_type.value}")
        print(f"[bold]Architecture:[/bold] {system_info.architecture.value}")
        print(f"[bold]WSL:[/bold] {'Yes' if system_info.is_wsl else 'No'}")
        if system_info.distro_version:
            print(f"[bold]Version:[/bold] {system_info.distro_version}")
        
        print()
        print(f"[bold]Package Manager:[/bold] {SystemDetector.get_package_manager(system_info.os_type) or 'N/A'}")
        print(f"[bold]Docker Installation Supported:[/bold] {'Yes' if SystemDetector.supports_docker_installation(system_info.os_type) else 'No'}")
        
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def install_azure_cli(force: bool = False, manual: bool = False) -> None:
    """
    Install Azure CLI automatically based on operating system.
    
    Args:
        force: Force reinstall even if already installed
        manual: Show manual installation instructions
    """
    try:
        system_info = SystemDetector.detect()
        azure_installer = AzureCliInstaller(system_info)
        
        print("[bold blue]Azure CLI Installation[/bold blue]")
        print(f"Detected system: [green]{system_info}[/green]")
        print()
        
        # Show manual instructions if requested
        if manual:
            azure_installer.print_manual_instructions()
            return
        
        # Check if already installed
        if not force and azure_installer.is_installed():
            version = azure_installer.get_installed_version()
            print(f"Azure CLI is already installed (version {version})")
            
            if not typer.confirm("Do you want to reinstall?"):
                return
        
        # Install Azure CLI
        print()
        success = azure_installer.install()
        
        if success:
            print()
            print("[bold green]Azure CLI installed successfully![/bold green]")
            print("Test with: [cyan]az --version[/cyan]")
        else:
            print()
            print("[bold red]Automatic installation failed.[/bold red]")
            print()
            azure_installer.print_manual_instructions()
            raise typer.Exit(code=1)
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def install_terraform(force: bool = False, manual: bool = False) -> None:
    """
    Install Terraform automatically based on operating system.
    
    Args:
        force: Force reinstall even if already installed
        manual: Show manual installation instructions
    """
    try:
        system_info = SystemDetector.detect()
        terraform_installer = TerraformInstaller(system_info)
        
        print("[bold blue]Terraform Installation[/bold blue]")
        print(f"Detected system: [green]{system_info}[/green]")
        print()
        
        # Show manual instructions if requested
        if manual:
            terraform_installer.print_manual_instructions()
            return
        
        # Check if already installed
        if not force and terraform_installer.is_installed():
            version = terraform_installer.get_installed_version()
            print(f"Terraform is already installed (version {version})")
            
            if not typer.confirm("Do you want to reinstall?"):
                return
        
        # Install Terraform
        print()
        success = terraform_installer.install()
        
        if success:
            print()
            print("[bold green]Terraform installed successfully![/bold green]")
            print("Test with: [cyan]terraform --version[/cyan]")
        else:
            print()
            print("[bold red]Automatic installation failed.[/bold red]")
            print()
            terraform_installer.print_manual_instructions()
            raise typer.Exit(code=1)
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)


def install_aws_cli(force: bool = False, manual: bool = False) -> None:
    """
    Install AWS CLI v2 automatically based on operating system.
    
    Args:
        force: Force reinstall even if already installed
        manual: Show manual installation instructions
    """
    try:
        system_info = SystemDetector.detect()
        aws_installer = AwsCliInstaller(system_info)
        
        print("[bold blue]AWS CLI v2 Installation[/bold blue]")
        print(f"Detected system: [green]{system_info}[/green]")
        print()
        
        # Show manual instructions if requested
        if manual:
            aws_installer.print_manual_instructions()
            return
        
        # Check if already installed
        if not force and aws_installer.is_installed():
            version = aws_installer.get_installed_version()
            print(f"AWS CLI v2 is already installed (version {version})")
            
            if not typer.confirm("Do you want to reinstall?"):
                return
        
        # Install AWS CLI
        print()
        success = aws_installer.install()
        
        if success:
            print()
            print("[bold green]AWS CLI v2 installed successfully![/bold green]")
            print("Test with: [cyan]aws --version[/cyan]")
        else:
            print()
            print("[bold red]Automatic installation failed.[/bold red]")
            print()
            aws_installer.print_manual_instructions()
            raise typer.Exit(code=1)
            
    except Exception as e:
        print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(code=1)