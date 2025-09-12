# 🚀 CLI Leme DevOps

[![PyPI version](https://badge.fury.io/py/leme.svg)](https://badge.fury.io/py/leme)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Configuração automática do seu ambiente DevOps em 2 comandos!**

Esta CLI instala e configura automaticamente todas as ferramentas necessárias para desenvolvimento DevOps, incluindo Docker, Git, Terraform, Azure CLI, AWS CLI, kubectl, Ansible e muito mais.

## ⚡ Instalação Super Rápida

```bash
# Instalar via pip
pip install leme

# Configurar ambiente completo
leme setup
```

**Pronto!** 🎉 Todas as ferramentas DevOps estão configuradas e prontas para uso.

## ✅ Ferramentas Suportadas

### 🔧 **Essenciais**
- **🐳 Docker** - Plataforma de containerização
- **📦 Git** - Sistema de controle de versão

### ☁️ **Cloud & DevOps** (opcionais)
- **🏗️ Terraform** - Infraestrutura como código
- **☁️ AWS CLI v2** - Interface da Amazon Web Services
- **🔵 Azure CLI** - Interface do Microsoft Azure
- **⚙️ kubectl** - Gerenciamento de clusters Kubernetes
- **🤖 Ansible** - Automação de configuração
- **👀 watch** - Monitoramento de comandos

## 🚀 Comandos Principais

### Configuração Inicial
```bash
# Configurar ambiente completo (modo interativo)
leme setup

# Instalar tudo automaticamente sem perguntar
leme setup --force

# Ver status de todas as ferramentas
leme status
```

### Instalação Individual
```bash
# Instalar ferramentas específicas
leme install docker
leme install terraform
leme install azure
leme install aws
```

### Informações do Sistema
```bash
# Ver informações do sistema operacional
leme info

# Verificar versão da CLI
leme --version

# Ajuda completa
leme --help
```

## 🎯 Modo Interativo (Padrão)

Por padrão, `leme setup` pergunta quais ferramentas opcionais você deseja instalar:

```bash
$ leme setup

🚀 CLI Leme DevOps - Setup do Ambiente DevOps

🔍 Verificando ambiente atual...
📊 Ferramentas encontradas:
  • Docker: ❌ Não instalado
  • Git: ✅ Instalado (v2.39.0)
  • Terraform: ❌ Não instalado

❓ Escolha as ferramentas para instalar:

• Terraform (opcional)
  Ferramenta de infraestrutura como código
  Deseja instalar Terraform? [y/N]: y

• Azure CLI (opcional)
  Interface de linha de comando da Azure
  Deseja instalar Azure CLI? [y/N]: n

...
```

## 🛠️ Opções Avançadas

```bash
# Apenas verificar o que está instalado
leme setup --check-only

# Instalar apenas ferramentas essenciais
leme setup --required-only

# Pular instalação do Docker
leme setup --skip-docker

# Instalar ferramentas específicas
leme setup --tools docker,terraform,azure

# Forçar reinstalação
leme setup --force
```

## 💻 Sistemas Suportados

| Sistema Operacional | Status | Métodos de Instalação |
|---------------------|--------|-----------------------|
| **Ubuntu 20.04+** | ✅ Totalmente Testado | apt + repositórios oficiais |
| **Debian 11+** | ✅ Totalmente Testado | apt + repositórios oficiais |
| **macOS 12+** | ✅ Funcional | Homebrew + instaladores oficiais |
| **WSL Ubuntu** | ✅ Testado | apt + repositórios oficiais |
| **CentOS/RHEL 8+** | ⚠️ Funcional | yum/dnf + repositórios oficiais |
| **Fedora 35+** | ⚠️ Funcional | dnf + repositórios oficiais |

**Arquiteturas**: x86_64 (Intel/AMD) e ARM64 (Apple Silicon/ARM)

## 🔧 Exemplos de Uso

### Para Estudantes - Configuração Completa
```bash
# Instalar a CLI
pip install leme

# Configurar ambiente para curso DevOps
leme setup

# Verificar se tudo funcionou
leme status
docker run hello-world
```

### Para Desenvolvedores - Instalação Seletiva
```bash
# Instalar apenas Docker e Terraform
leme setup --tools docker,terraform

# Adicionar AWS CLI depois
leme install aws

# Verificar configuração final
leme status
```

### Para CI/CD - Instalação Automatizada
```bash
# Instalar tudo sem interação
leme setup --force

# Verificar instalação em scripts
leme status --check-only
```

## 🆘 Solução de Problemas

### Docker não funciona após instalação (Linux)
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Testar
docker run hello-world
```

### Python/pip não encontrado
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3 python3-pip

# macOS
brew install python3

# Windows - Baixar de python.org
```

### Ferramentas não detectadas
```bash
# Forçar verificação completa
leme setup --force

# Ver informações de debug
leme info
```

## 🧪 Desenvolvimento Local

```bash
# Clonar repositório
git clone https://github.com/iesodias/projeto_cli.git
cd projeto_cli

# Instalar em modo desenvolvimento
pip install -e .

# Testar comando
leme --help
```

## 📚 Documentação

- **[Guia Completo](https://github.com/iesodias/projeto_cli#readme)** - Documentação completa
- **[Exemplos](https://github.com/iesodias/projeto_cli/tree/main/examples)** - Scripts de exemplo
- **[Troubleshooting](https://github.com/iesodias/projeto_cli/wiki/Troubleshooting)** - Solução de problemas

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua feature branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🎯 Resumo - Quick Start

```bash
# 🚀 INSTALAÇÃO E USO
pip install leme                    # Instalar CLI
leme setup                         # Configurar ambiente (interativo)
leme status                        # Verificar instalação

# 🔧 COMANDOS ÚTEIS
leme setup --force                 # Instalar tudo automaticamente
leme install docker               # Instalar ferramenta específica
leme info                         # Informações do sistema
leme --help                       # Ajuda completa
```

**A CLI detecta seu sistema automaticamente e instala tudo corretamente!** 🎯