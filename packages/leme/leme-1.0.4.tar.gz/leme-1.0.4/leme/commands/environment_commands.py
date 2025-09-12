"""Commands for DevOps environment configuration."""

import subprocess
import typer
from rich import print
from typing import Optional, List

from ..system.environment_manager import EnvironmentManager
from ..system.docker_installer import DockerInstaller
from ..system.installers.git_installer import GitInstaller
from ..system.installers.terraform_installer import TerraformInstaller
from ..system.installers.aws_cli_installer import AwsCliInstaller
from ..system.installers.azure_cli_installer import AzureCliInstaller
from ..config.constants import Tool, DEVOPS_TOOLS_CONFIG


def setup_environment(
    check_only: bool = typer.Option(False, "--check-only", help="Only check current environment"),
    required_only: bool = typer.Option(False, "--required-only", help="Install only required tools"),
    skip_docker: bool = typer.Option(False, "--skip-docker", help="Skip Docker installation"),
    force: bool = typer.Option(False, "--force", "-f", help="Force tool reinstallation"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive mode (LEGACY - now default)"),
    tools: Optional[List[str]] = typer.Option(None, "--tools", "-t", help="Install only specific tools (e.g: git,docker)")
) -> None:
    """
    Configure complete DevOps environment for the course.
    
    This command checks and installs all necessary tools:
    - Docker (required)
    - Git (required) 
    - Azure CLI (optional)
    - AWS CLI v2 (optional)
    - kubectl (optional)
    - Ansible (optional)
    - watch (optional)
    """
    print("[bold green]DevOps Environment Setup[/bold green]")
    print()
    
    # Initialize manager
    env_manager = EnvironmentManager()
    
    # Check-only mode
    if check_only:
        env_manager.show_status_report()
        return
    
    # Check current status
    print("[bold blue]Checking current environment...[/bold blue]")
    env_manager.check_all_tools()
    env_manager.show_status_report()
    
    # Determine tools to install
    if tools:
        # Specific list of tools
        selected_tools = []
        for tool_name in tools:
            try:
                tool = Tool(tool_name.lower())
                selected_tools.append(tool)
            except ValueError:
                print(f"[yellow]Unknown tool: {tool_name}[/yellow]")
        
        if not selected_tools:
            print("[red]No valid tools specified[/red]")
            raise typer.Exit(1)
        
        tools_to_install = [t for t in selected_tools if not env_manager.tools_status.get(t, None) or not env_manager.tools_status[t].installed]
    
    elif required_only:
        # Only required tools
        tools_to_install = env_manager.get_missing_tools(only_required=True)
    
    else:
        # All non-installed tools
        tools_to_install = env_manager.get_missing_tools(only_required=False)
    
    # Filter Docker if requested
    if skip_docker and Tool.DOCKER in tools_to_install:
        tools_to_install.remove(Tool.DOCKER)
        print("[blue]Docker will be skipped as requested[/blue]")
    
    # Check if there's anything to install
    if not tools_to_install:
        print("[green]All selected tools are already installed![/green]")
        return
    
    # Always ask for optional tools (except if --force)
    if not force:
        print(f"\n[bold cyan]Choose tools to install:[/bold cyan]")
        selected_tools = []
        
        for tool in tools_to_install:
            config = DEVOPS_TOOLS_CONFIG[tool]
            required_text = "[red](required)[/red]" if config["required"] else "[yellow](optional)[/yellow]"
            
            print(f"\n• [blue]{config['name']}[/blue] {required_text}")
            print(f"  {config['description']}")
            
            # All tools are now optional - ask for all
            confirm = typer.confirm(f"  Do you want to install {config['name']}?")
            if confirm:
                selected_tools.append(tool)
            else:
                print(f"  [yellow]Skipping {config['name']}[/yellow]")
        
        tools_to_install = selected_tools
        
        if not tools_to_install:
            print("\n[yellow]No tools selected for installation[/yellow]")
            return
        
        print(f"\n[bold green]Tools selected for installation:[/bold green]")
        for tool in tools_to_install:
            config = DEVOPS_TOOLS_CONFIG[tool]
            print(f"  • [blue]{config['name']}[/blue]")
    
    else:
        # Force mode - install everything without asking
        print(f"\n[bold cyan]Force Mode - Installing all tools:[/bold cyan]")
        for tool in tools_to_install:
            config = DEVOPS_TOOLS_CONFIG[tool]
            required_text = "[red](required)[/red]" if config["required"] else "[yellow](optional)[/yellow]"
            print(f"  • [blue]{config['name']}[/blue] {required_text} - {config['description']}")
    
    print("\n[bold green]Starting tool installation...[/bold green]")
    
    # Install tools one by one
    success_count = 0
    for tool in tools_to_install:
        config = DEVOPS_TOOLS_CONFIG[tool]
        print(f"\n[bold blue]Installing {config['name']}...[/bold blue]")
        
        try:
            success = _install_tool(tool, env_manager.system_info, force)
            if success:
                print(f"[green]{config['name']} installed successfully![/green]")
                success_count += 1
            else:
                print(f"[red]Failed to install {config['name']}[/red]")
        
        except Exception as e:
            print(f"[red]Error installing {config['name']}: {str(e)}[/red]")
    
    # Final report
    print(f"\n[bold cyan]Installation Report:[/bold cyan]")
    print(f"  • [green]Successfully installed:[/green] {success_count}")
    print(f"  • [red]Failed:[/red] {len(tools_to_install) - success_count}")
    
    # Check final environment
    print("\n[bold blue]Checking environment after installation...[/bold blue]")
    env_manager.check_all_tools()
    env_manager.show_status_report()
    
    # Final status
    if env_manager.is_environment_ready():
        print("\n[bold green]DevOps environment configured successfully![/bold green]")
        print("[blue]You are ready for the course![/blue]")
    else:
        missing = env_manager.get_missing_tools(only_required=True)
        print(f"\n[yellow]Still missing some required tools: {[DEVOPS_TOOLS_CONFIG[t]['name'] for t in missing]}[/yellow]")
        print("[blue]Run the command again to try installing the missing tools[/blue]")


def environment_status() -> None:
    """Show current status of all DevOps tools."""
    env_manager = EnvironmentManager()
    env_manager.show_status_report()


def _install_tool(tool: Tool, system_info, force: bool = False) -> bool:
    """
    Install a specific tool.
    
    Args:
        tool: Tool to be installed
        system_info: System information
        force: Force reinstallation
        
    Returns:
        bool: True if installation was successful
    """
    try:
        if tool == Tool.DOCKER:
            # Docker already has dedicated installer
            docker_installer = DockerInstaller()
            return docker_installer.install(force=force, test_after_install=True)
        
        elif tool == Tool.GIT:
            return _install_git(system_info)
        
        elif tool == Tool.TERRAFORM:
            return _install_terraform(system_info)
        
        elif tool == Tool.AZURE_CLI:
            return _install_azure_cli(system_info)
        
        elif tool == Tool.AWS_CLI:
            return _install_aws_cli(system_info)
        
        elif tool == Tool.KUBECTL:
            return _install_kubectl(system_info)
        
        elif tool == Tool.ANSIBLE:
            return _install_ansible(system_info)
        
        elif tool == Tool.WATCH:
            return _install_watch(system_info)
        
        else:
            print(f"[yellow]Installer for {tool.value} not implemented yet[/yellow]")
            return False
    
    except Exception as e:
        print(f"[red]Error during installation of {tool.value}: {str(e)}[/red]")
        return False


def _install_git(system_info) -> bool:
    """Install Git based on operating system."""
    try:
        git_installer = GitInstaller(system_info)
        return git_installer.install()
    except Exception as e:
        print(f"[red]Error during Git installation: {str(e)}[/red]")
        return False


def _install_terraform(system_info) -> bool:
    """Install Terraform based on operating system."""
    try:
        terraform_installer = TerraformInstaller(system_info)
        return terraform_installer.install()
    except Exception as e:
        print(f"[red]Error during Terraform installation: {str(e)}[/red]")
        return False


def _install_azure_cli(system_info) -> bool:
    """Install Azure CLI based on operating system."""
    try:
        azure_installer = AzureCliInstaller(system_info)
        return azure_installer.install()
    except Exception as e:
        print(f"[red]Error during Azure CLI installation: {str(e)}[/red]")
        return False


def _install_aws_cli(system_info) -> bool:
    """Install AWS CLI v2 based on operating system."""
    try:
        aws_installer = AwsCliInstaller(system_info)
        return aws_installer.install()
    except Exception as e:
        print(f"[red]Error during AWS CLI installation: {str(e)}[/red]")
        return False


def _install_kubectl(system_info) -> bool:
    """Install kubectl based on operating system."""
    try:
        from ..system.system_detector import OperatingSystem
        
        print("[blue]Installing kubectl...[/blue]")
        
        if system_info.os_type in [
            OperatingSystem.UBUNTU, OperatingSystem.WSL_UBUNTU,
            OperatingSystem.DEBIAN, OperatingSystem.WSL_DEBIAN
        ]:
            # Ubuntu/Debian - via official Kubernetes repository
            # Clean corrupted repositories first
            _cleanup_corrupted_repositories()
            subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
            subprocess.run([
                "sudo", "apt-get", "install", "-y", "ca-certificates", "curl", "apt-transport-https"
            ], check=True, capture_output=True)
            
            # Add Kubernetes GPG key
            subprocess.run([
                "sudo", "mkdir", "-p", "/etc/apt/keyrings"
            ], capture_output=True)
            subprocess.run([
                "bash", "-c", 
                "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg"
            ], check=True, capture_output=True)
            
            # Add repository
            subprocess.run([
                "bash", "-c",
                "echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list"
            ], check=True, capture_output=True)
            
            subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "kubectl"], check=True, capture_output=True)
            
        elif system_info.os_type == OperatingSystem.MACOS:
            # macOS - via Homebrew
            subprocess.run(["brew", "install", "kubectl"], check=True, capture_output=True)
            
        elif system_info.os_type in [OperatingSystem.CENTOS, OperatingSystem.RHEL, OperatingSystem.FEDORA]:
            # CentOS/RHEL/Fedora - via official repository
            repo_content = """[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/repodata/repomd.xml.key"""
            
            subprocess.run([
                "bash", "-c", f"echo '{repo_content}' | sudo tee /etc/yum.repos.d/kubernetes.repo"
            ], check=True)
            
            pkg_manager = "dnf" if system_info.os_type == OperatingSystem.FEDORA else "yum"
            subprocess.run(["sudo", pkg_manager, "install", "-y", "kubectl"], check=True, capture_output=True)
        
        else:
            print("[yellow]System not supported for kubectl[/yellow]")
            return False
            
        print("[green]kubectl installed successfully![/green]")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[red]Error installing kubectl: {e}[/red]")
        return False
    except Exception as e:
        print(f"[red]Unexpected error installing kubectl: {str(e)}[/red]")
        return False


def _install_ansible(system_info) -> bool:
    """Install Ansible based on operating system."""
    try:
        from ..system.system_detector import OperatingSystem
        
        print("[blue]Installing Ansible...[/blue]")
        
        if system_info.os_type in [
            OperatingSystem.UBUNTU, OperatingSystem.WSL_UBUNTU,
            OperatingSystem.DEBIAN, OperatingSystem.WSL_DEBIAN
        ]:
            # Ubuntu/Debian - via pip (método mais confiável)
            # Limpar repositórios corrompidos primeiro
            _cleanup_corrupted_repositories()
            subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "python3-pip"], check=True, capture_output=True)
            
            # Instalar Ansible globalmente para que fique disponível no PATH
            subprocess.run(["sudo", "pip3", "install", "ansible"], check=True, capture_output=True)
            
            # Verificar se o binário está acessível e criar link se necessário
            try:
                subprocess.run(["ansible", "--version"], check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Se não encontrar, tentar criar link simbólico
                ansible_paths = [
                    "/usr/local/bin/ansible",
                    "/home/user/.local/bin/ansible",
                    "/usr/bin/ansible"
                ]
                for path in ansible_paths:
                    if subprocess.run(["test", "-f", path], capture_output=True).returncode == 0:
                        subprocess.run(["sudo", "ln", "-sf", path, "/usr/bin/ansible"], capture_output=True)
                        break
            
        elif system_info.os_type == OperatingSystem.MACOS:
            # macOS - via Homebrew
            subprocess.run(["brew", "install", "ansible"], check=True, capture_output=True)
            
        elif system_info.os_type in [OperatingSystem.CENTOS, OperatingSystem.RHEL, OperatingSystem.FEDORA]:
            # CentOS/RHEL/Fedora - via pip
            pkg_manager = "dnf" if system_info.os_type == OperatingSystem.FEDORA else "yum"
            subprocess.run(["sudo", pkg_manager, "install", "-y", "python3-pip"], check=True, capture_output=True)
            
            # Instalar Ansible globalmente
            subprocess.run(["sudo", "pip3", "install", "ansible"], check=True, capture_output=True)
            
            # Verificar se o binário está acessível
            try:
                subprocess.run(["ansible", "--version"], check=True, capture_output=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Se não encontrar, tentar criar link simbólico
                ansible_paths = [
                    "/usr/local/bin/ansible",
                    "/home/user/.local/bin/ansible",
                    "/usr/bin/ansible"
                ]
                for path in ansible_paths:
                    if subprocess.run(["test", "-f", path], capture_output=True).returncode == 0:
                        subprocess.run(["sudo", "ln", "-sf", path, "/usr/bin/ansible"], capture_output=True)
                        break
        
        else:
            print("[yellow]System not supported for Ansible[/yellow]")
            return False
            
        print("[green]Ansible installed successfully![/green]")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[red]Error installing Ansible: {e}[/red]")
        return False
    except Exception as e:
        print(f"[red]Unexpected error installing Ansible: {str(e)}[/red]")
        return False


def _install_watch(system_info) -> bool:
    """Install watch based on operating system."""
    try:
        from ..system.system_detector import OperatingSystem
        
        print("[blue]Installing watch...[/blue]")
        
        if system_info.os_type in [
            OperatingSystem.UBUNTU, OperatingSystem.WSL_UBUNTU,
            OperatingSystem.DEBIAN, OperatingSystem.WSL_DEBIAN
        ]:
            # Ubuntu/Debian - via apt
            # Limpar repositórios corrompidos primeiro
            _cleanup_corrupted_repositories()
            subprocess.run(["sudo", "apt-get", "update"], check=True, capture_output=True)
            subprocess.run(["sudo", "apt-get", "install", "-y", "procps"], check=True, capture_output=True)
            
        elif system_info.os_type == OperatingSystem.MACOS:
            # macOS - via Homebrew
            subprocess.run(["brew", "install", "watch"], check=True, capture_output=True)
            
        elif system_info.os_type in [OperatingSystem.CENTOS, OperatingSystem.RHEL, OperatingSystem.FEDORA]:
            # CentOS/RHEL/Fedora - via yum/dnf
            pkg_manager = "dnf" if system_info.os_type == OperatingSystem.FEDORA else "yum"
            subprocess.run(["sudo", pkg_manager, "install", "-y", "procps-ng"], check=True, capture_output=True)
        
        else:
            print("[yellow]System not supported for watch[/yellow]")
            return False
            
        print("[green]watch installed successfully![/green]")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[red]Error installing watch: {e}[/red]")
        return False
    except Exception as e:
        print(f"[red]Unexpected error installing watch: {str(e)}[/red]")
        return False


def _cleanup_corrupted_repositories() -> None:
    """Remove corrupted repositories that can affect apt-get update."""
    try:
        print("[blue]Cleaning corrupted repositories...[/blue]")
        
        # Lista de arquivos de repositório que podem estar corrompidos
        corrupted_repos = [
            "/etc/apt/sources.list.d/hashicorp.list",
            "/etc/apt/sources.list.d/microsoft-prod.list",
            "/etc/apt/sources.list.d/azure-cli.list",
            "/etc/apt/sources.list.d/kubernetes.list"
        ]
        
        # Lista de chaves GPG que podem estar corrompidas
        corrupted_keys = [
            "/etc/apt/keyrings/hashicorp.gpg",
            "/etc/apt/keyrings/microsoft.gpg",
            "/etc/apt/keyrings/kubernetes-apt-keyring.gpg",
            "/etc/apt/trusted.gpg.d/microsoft.gpg"
        ]
        
        # Remover arquivos de repositório corrompidos
        for repo_file in corrupted_repos:
            subprocess.run([
                "sudo", "rm", "-f", repo_file
            ], capture_output=True)
        
        # Remover chaves GPG corrompidas
        for key_file in corrupted_keys:
            subprocess.run([
                "sudo", "rm", "-f", key_file
            ], capture_output=True)
        
        # Tentar atualizar repositórios para limpar cache
        result = subprocess.run([
            "sudo", "apt-get", "update"
        ], capture_output=True)
        
        if result.returncode == 0:
            print("[green]Repositories cleaned successfully[/green]")
        else:
            print("[yellow]Warning: Some repositories may still have issues[/yellow]")
        
    except Exception as e:
        print(f"[yellow]Warning: Could not clean repositories: {str(e)}[/yellow]")