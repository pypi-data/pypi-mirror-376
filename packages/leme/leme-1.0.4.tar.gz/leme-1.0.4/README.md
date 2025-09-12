# Leme DevOps CLI

[![PyPI version](https://badge.fury.io/py/leme.svg)](https://badge.fury.io/py/leme)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automatic DevOps environment setup in 2 commands!**

This CLI automatically installs and configures all necessary tools for DevOps development, including Docker, Git, Terraform, Azure CLI, AWS CLI, kubectl, Ansible and much more.

## Quick Installation

```bash
# Install via pip
pip install leme

# Setup complete environment
leme setup
```

**Done!** All DevOps tools are configured and ready to use.

## Supported Tools

### **Essential**
- **Docker** - Containerization platform
- **Git** - Version control system

### **Cloud & DevOps** (optional)
- **Terraform** - Infrastructure as code
- **AWS CLI v2** - Amazon Web Services interface
- **Azure CLI** - Microsoft Azure interface
- **kubectl** - Kubernetes cluster management
- **Ansible** - Configuration automation
- **watch** - Command monitoring

## Main Commands

### Initial Setup
```bash
# Setup complete environment (interactive mode)
leme setup

# Install everything automatically without asking
leme setup --force

# View status of all tools
leme status
```

### Individual Installation
```bash
# Install specific tools
leme install docker
leme install terraform
leme install azure
leme install aws
```

### System Information
```bash
# View operating system information
leme info

# Check CLI version
leme --version

# Complete help
leme --help
```

## Interactive Mode (Default)

By default, `leme setup` asks which optional tools you want to install:

```bash
$ leme setup

Leme DevOps CLI - DevOps Environment Setup

Checking current environment...
Found tools:
  • Docker: Not installed
  • Git: Installed (v2.39.0)
  • Terraform: Not installed

Choose tools to install:

• Terraform (optional)
  Infrastructure as code tool
  Install Terraform? [y/N]: y

• Azure CLI (optional)
  Azure command line interface
  Install Azure CLI? [y/N]: n

...
```

## Advanced Options

```bash
# Only check what's installed
leme setup --check-only

# Install only essential tools
leme setup --required-only

# Skip Docker installation
leme setup --skip-docker

# Install specific tools
leme setup --tools docker,terraform,azure

# Force reinstallation
leme setup --force
```

## Supported Systems

| Operating System | Status | Installation Methods |
|------------------|--------|---------------------|
| **Ubuntu 20.04+** | Fully Tested | apt + official repositories |
| **Debian 11+** | Fully Tested | apt + official repositories |
| **macOS 12+** | Functional | Homebrew + official installers |
| **WSL Ubuntu** | Tested | apt + official repositories |
| **CentOS/RHEL 8+** | Functional | yum/dnf + official repositories |
| **Fedora 35+** | Functional | dnf + official repositories |

**Architectures**: x86_64 (Intel/AMD) and ARM64 (Apple Silicon/ARM)

## Usage Examples

### For Students - Complete Setup
```bash
# Install the CLI
pip install leme

# Setup environment for DevOps course
leme setup

# Verify everything worked
leme status
docker run hello-world
```

### For Developers - Selective Installation
```bash
# Install only Docker and Terraform
leme setup --tools docker,terraform

# Add AWS CLI later
leme install aws

# Check final configuration
leme status
```

### For CI/CD - Automated Installation
```bash
# Install everything without interaction
leme setup --force

# Check installation in scripts
leme status --check-only
```

## Troubleshooting

### Docker doesn't work after installation (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Test
docker run hello-world
```

### Python/pip not found
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip

# macOS
brew install python3

# Windows - Download from python.org
```

### Tools not detected
```bash
# Force complete verification
leme setup --force

# View debug information
leme info
```

## Local Development

```bash
# Clone repository
git clone https://github.com/iesodias/projeto_cli.git
cd projeto_cli

# Install in development mode
pip install -e .

# Test command
leme --help
```

## Documentation

- **[Complete Guide](https://github.com/iesodias/projeto_cli#readme)** - Full documentation
- **[Examples](https://github.com/iesodias/projeto_cli/tree/main/examples)** - Example scripts
- **[Troubleshooting](https://github.com/iesodias/projeto_cli/wiki/Troubleshooting)** - Problem solving

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Quick Start Summary

```bash
# INSTALLATION AND USAGE
pip install leme                    # Install CLI
leme setup                         # Setup environment (interactive)
leme status                        # Check installation

# USEFUL COMMANDS
leme setup --force                 # Install everything automatically
leme install docker               # Install specific tool
leme info                         # System information
leme --help                       # Complete help
```

**The CLI automatically detects your system and installs everything correctly!**