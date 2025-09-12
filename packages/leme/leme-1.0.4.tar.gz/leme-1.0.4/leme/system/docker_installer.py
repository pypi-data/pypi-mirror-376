"""Main manager for Docker installation."""

from typing import Optional
from rich import print
import typer

from .system_detector import SystemDetector, SystemInfo, OperatingSystem
from .installers.base_installer import BaseInstaller
from .installers.ubuntu_installer import UbuntuInstaller
from .installers.macos_installer import MacOSInstaller
from .installers.redhat_installer import RedHatInstaller


class DockerInstaller:
    """Main manager for Docker installation."""
    
    def __init__(self):
        """Initialize the Docker installer."""
        self.system_info = SystemDetector.detect()
        self.installer = self._get_installer()
    
    def _get_installer(self) -> Optional[BaseInstaller]:
        """
        Retorna o instalador apropriado para o sistema.
        
        Returns:
            Optional[BaseInstaller]: Instalador ou None se não suportado
        """
        if self.system_info.os_type in [
            OperatingSystem.UBUNTU, OperatingSystem.WSL_UBUNTU,
            OperatingSystem.DEBIAN, OperatingSystem.WSL_DEBIAN
        ]:
            return UbuntuInstaller(self.system_info)
        
        elif self.system_info.os_type == OperatingSystem.MACOS:
            return MacOSInstaller(self.system_info)
        
        elif self.system_info.os_type in [
            OperatingSystem.CENTOS, OperatingSystem.RHEL, OperatingSystem.FEDORA
        ]:
            return RedHatInstaller(self.system_info)
        
        return None
    
    def install(self, force: bool = False, test_after_install: bool = True) -> bool:
        """
        Instala o Docker no sistema.
        
        Args:
            force: Forçar reinstalação mesmo se já estiver instalado
            test_after_install: Testar instalação após completar
            
        Returns:
            bool: True se a instalação foi bem-sucedida
        """
        print(f"[bold blue]Docker Installation[/bold blue]")
        print(f"Detected system: [green]{self.system_info}[/green]")
        print()
        
        # Verificar se o sistema é suportado
        if not self.installer:
            print(f"[bold red]System not supported:[/bold red] {self.system_info.os_type.value}")
            print("Sistemas suportados: Ubuntu, Debian, CentOS, RHEL, Fedora, macOS")
            return False
        
        # Verificar se já está instalado
        if not force and self.installer.is_docker_installed():
            version = self.installer.get_docker_version()
            print(f":white_check_mark: Docker já está instalado (versão {version})")
            
            if not typer.confirm("Deseja reinstalar?"):
                return True
        
        # Verificar pré-requisitos
        if not self.installer.check_prerequisites():
            print(":x: [bold red]Pré-requisitos não atendidos.[/bold red]")
            return False
        
        # Instalar Docker
        print()
        success = self.installer.install()
        
        if not success:
            print()
            print(":x: [bold red]Falha na instalação automática.[/bold red]")
            print()
            self.installer.print_manual_instructions()
            return False
        
        # Testar instalação
        if test_after_install:
            print()
            test_result = self.installer.test_docker_installation()
            if test_result:
                print()
                print(":whale: [bold green]Docker instalado e funcionando![/bold green]")
            else:
                print()
                print(":warning: [bold yellow]Docker instalado mas pode não estar funcionando corretamente.[/bold yellow]")
                self._handle_docker_permission_issues()
        
        return True
    
    def _handle_docker_permission_issues(self) -> None:
        """Lida com problemas comuns de permissão do Docker."""
        print()
        print(":information_source: [bold cyan]Diagnóstico de Problemas Comuns:[/bold cyan]")
        
        # Verificar se é problema de permissão (apenas Linux)
        if self.system_info.os_type != OperatingSystem.MACOS:
            import subprocess
            import os
            
            # Verificar se usuário está no grupo docker
            try:
                result = subprocess.run(["groups"], capture_output=True, text=True)
                groups = result.stdout.strip()
                
                if "docker" not in groups:
                    print(":warning: [yellow]Problema identificado: Usuário não está no grupo 'docker'[/yellow]")
                    print()
                    print("[bold]Soluções:[/bold]")
                    print("1. [blue]Adicionar usuário ao grupo docker:[/blue]")
                    print(f"   sudo usermod -aG docker {os.getenv('USER', 'seu_usuario')}")
                    print("   newgrp docker")
                    print()
                    print("2. [blue]Ou fazer logout/login para aplicar as permissões[/blue]")
                    print()
                    print("3. [blue]Ou reiniciar o sistema[/blue]")
                    print()
                    
                    # Tentar adicionar automaticamente se confirmado
                    import typer
                    if typer.confirm("Deseja tentar adicionar automaticamente ao grupo docker?"):
                        try:
                            subprocess.run([
                                "sudo", "usermod", "-aG", "docker", os.getenv('USER', 'user')
                            ], check=True)
                            print(":white_check_mark: [green]Usuário adicionado ao grupo docker![/green]")
                            print(":information: [blue]Execute 'newgrp docker' ou faça logout/login para aplicar[/blue]")
                        except subprocess.CalledProcessError:
                            print(":x: [red]Falha ao adicionar usuário ao grupo docker[/red]")
                else:
                    print(":white_check_mark: [green]Usuário já está no grupo docker[/green]")
                    
            except Exception:
                pass
        
        # Verificar se Docker daemon está rodando
        try:
            result = subprocess.run(["docker", "version"], capture_output=True, text=True)
            if "Cannot connect to the Docker daemon" in result.stderr:
                print(":warning: [yellow]Docker daemon não está rodando[/yellow]")
                print()
                print("[bold]Soluções:[/bold]")
                if self.system_info.os_type == OperatingSystem.MACOS:
                    print("1. [blue]Abrir Docker Desktop:[/blue]")
                    print("   open /Applications/Docker.app")
                else:
                    print("1. [blue]Iniciar Docker daemon:[/blue]")
                    print("   sudo systemctl start docker")
                    print("   sudo systemctl enable docker")
                print()
        except Exception:
            pass
        
        print("[bold]Para mais ajuda:[/bold]")
        print("• Documentação: https://docs.docker.com/engine/install/linux-postinstall/")
        print("• Tente: python3 main.py environment-status")
    
    def uninstall(self) -> bool:
        """
        Remove o Docker do sistema.
        
        Returns:
            bool: True se a remoção foi bem-sucedida
        """
        if not self.installer:
            print(f"[bold red]System not supported:[/bold red] {self.system_info.os_type.value}")
            return False
        
        if not self.installer.is_docker_installed():
            print(":information: Docker não está instalado.")
            return True
        
        print(":warning: [bold yellow]Esta ação removerá o Docker completamente do sistema.[/bold yellow]")
        if not typer.confirm("Tem certeza que deseja continuar?"):
            return False
        
        return self.installer.uninstall()
    
    def check_installation(self) -> dict:
        """
        Verifica o status da instalação do Docker.
        
        Returns:
            dict: Informações sobre a instalação
        """
        info = {
            "system": str(self.system_info),
            "supported": self.installer is not None,
            "installed": False,
            "version": None,
            "working": False
        }
        
        if self.installer:
            info["installed"] = self.installer.is_docker_installed()
            if info["installed"]:
                info["version"] = self.installer.get_docker_version()
                info["working"] = self.installer.test_docker_installation()
        
        return info
    
    def print_status(self) -> None:
        """Imprime o status atual da instalação."""
        info = self.check_installation()
        
        print(f"System: [bold]{info['system']}[/bold]")
        print(f"Supported: [bold]{'✓' if info['supported'] else '✗'}[/bold]")
        
        if info['supported']:
            if info['installed']:
                status_color = "green" if info['working'] else "yellow"
                status_icon = "✓" if info['working'] else "⚠"
                print(f"Docker: [bold][{status_color}]{status_icon} Installed (v{info['version']})[/{status_color}][/bold]")
                
                if not info['working']:
                    print("  [yellow]⚠ Docker pode não estar funcionando corretamente[/yellow]")
            else:
                print(f":whale: [bold]Docker:[/bold] [red]✗ Não instalado[/red]")
        else:
            print("  [red]Sistema não suportado para instalação automática[/red]")
    
    def get_manual_instructions(self) -> None:
        """Imprime instruções para instalação manual."""
        if not self.installer:
            print(f"[bold red]System not supported:[/bold red] {self.system_info.os_type.value}")
            print()
            print("[bold yellow]📋 Instalação Manual:[/bold yellow]")
            print("Visite: https://docs.docker.com/get-docker/")
            return
        
        self.installer.print_manual_instructions()