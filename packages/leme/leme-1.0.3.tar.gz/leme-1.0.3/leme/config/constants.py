"""Application constants and configurations."""

import enum
from pathlib import Path




class Tool(str, enum.Enum):
    """Tools that can be installed."""
    DOCKER = "docker"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    AZURE_CLI = "az"
    AWS_CLI = "aws"
    GIT = "git"
    KUBECTL = "kubectl"
    WATCH = "watch"


# Path configurations
BASE_PATH = Path(__file__).parent.parent.parent
SRC_PATH = BASE_PATH / "src"

# DevOps tools configurations
DEVOPS_TOOLS_CONFIG = {
    Tool.DOCKER: {
        "name": "Docker",
        "description": "Containerization platform",
        "check_command": ["docker", "--version"],
        "priority": 1,
        "required": False
    },
    Tool.TERRAFORM: {
        "name": "Terraform",
        "description": "Infrastructure as code tool",
        "check_command": ["terraform", "--version"],
        "priority": 2,
        "required": False
    },
    Tool.GIT: {
        "name": "Git",
        "description": "Version control system",
        "check_command": ["git", "--version"],
        "priority": 3,
        "required": False
    },
    Tool.AZURE_CLI: {
        "name": "Azure CLI",
        "description": "Azure command line interface",
        "check_command": ["az", "--version"],
        "priority": 4,
        "required": False
    },
    Tool.AWS_CLI: {
        "name": "AWS CLI v2",
        "description": "AWS command line interface",
        "check_command": ["aws", "--version"],
        "priority": 5,
        "required": False
    },
    Tool.KUBECTL: {
        "name": "kubectl",
        "description": "Kubernetes client",
        "check_command": ["kubectl", "version", "--client"],
        "priority": 6,
        "required": False
    },
    Tool.ANSIBLE: {
        "name": "Ansible",
        "description": "Automation and configuration management",
        "check_command": ["ansible", "--version"],
        "priority": 7,
        "required": False
    },
    Tool.WATCH: {
        "name": "watch",
        "description": "Execute commands periodically",
        "check_command": ["watch", "--version"],
        "priority": 8,
        "required": False
    }
}