FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Instalar Python 3.11 e ferramentas essenciais
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    curl \
    wget \
    git \
    vim \
    nano \
    gpg \
    && rm -rf /var/lib/apt/lists/*

# Criar links simbólicos para python
RUN ln -sf /usr/bin/python3.11 /usr/local/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python3

# Instalar ferramentas Python
RUN pip3 install --upgrade pip setuptools wheel

# --- SEÇÃO CORRIGIDA ---
# Instalar MongoDB Tools usando o método gpg keyring
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
    gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg \
    && echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y mongodb-mongosh mongodb-database-tools \
    && rm -rf /var/lib/apt/lists/*
# --- FIM DA SEÇÃO CORRIGIDA ---

# Configurar usuário vscode
USER vscode

# Copiar e instalar dependências de produção e desenvolvimento
COPY --chown=vscode:vscode requirements.txt requirements-dev.txt /tmp/pip-tmp/
RUN pip3 install --user -r /tmp/pip-tmp/requirements.txt && pip3 install --user -r /tmp/pip-tmp/requirements-dev.txt \
    && rm -rf /tmp/pip-tmp

# Configurar PATH para binários Python do usuário
ENV PATH="/home/vscode/.local/bin:$PATH"

WORKDIR /workspace

# Copia todo o código do projeto para o diretório de trabalho no contêiner
COPY --chown=vscode:vscode . .