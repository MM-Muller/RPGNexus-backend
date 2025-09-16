
<p align="center">
  <img src="https://raw.githubusercontent.com/MM-Muller/RPGNexus-frontend/main/src/assets/images/logo.png" alt="RPGNexus Logo" width="150"/>
</p>

<h1 align="center">RPGNexus Back-end API</h1>

<p align="center">
  <strong>API RESTful para o jogo de RPG textual com IA "RPGNexus".</strong><br>
  Parte do Projeto 2 do Programa Trainee em Inteligência Artificial (Wise Intelligence).
</p>

---

## 🚀 Sobre o Projeto

O RPGNexus é um sistema web de RPG textual que utiliza um modelo de linguagem (LLM) para criar narrativas dinâmicas e interativas. Este repositório contém o back-end da aplicação, desenvolvido em Python com o framework FastAPI, responsável por gerenciar toda a lógica de negócio, autenticação, personagens, campanhas e a integração com a IA.

## 🛠️ Tecnologias Principais

- **Linguagem:** Python 3.11
- **Framework:** FastAPI
- **Banco de Dados:** MongoDB
- **Autenticação:** JWT (JSON Web Tokens)
- **Inteligência Artificial:** LLM (Large Language Model) para geração de narrativas.
- **Containerização:** Docker e VS Code Dev Container

## ✨ Funcionalidades

- **Autenticação de Usuários:** Cadastro (`/signup`), login (`/login`) e verificação de usuário (`/me`) com JWT.
- **Gerenciamento de Personagens:** Criação, listagem, visualização de detalhes e exclusão de personagens.
- **Sistema de Campanhas:** Lógica para iniciar, consultar, interagir e encerrar campanhas.
- **Integração com LLM:** Geração de prompts dinâmicos com base no estado do jogo e processamento de respostas em JSON.
- **Persistência de Dados:** Armazenamento de usuários, personagens e históricos de campanha no MongoDB.

---

## 🏁 Começando

Estas instruções permitirão que você tenha uma cópia do projeto em operação na sua máquina local para desenvolvimento e testes.

### Pré-requisitos

- Docker e Docker Compose
- Visual Studio Code com a extensão [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### 🐳 Executando com Dev Container (Recomendado)

Este projeto está configurado para ser executado em um ambiente de desenvolvimento containerizado, o que simplifica a configuração.

1.  Clone o repositório:
    ```bash
    git clone https://github.com/MM-Muller/RPGNexus-backend
    cd rpgnexus-backend
    ```
2.  Abra o projeto no VS Code.
3.  O VS Code irá sugerir **"Reopen in Container"**. Clique nesta opção.
4.  Aguarde o Docker construir a imagem e iniciar o container. O FastAPI será iniciado automaticamente.

O servidor estará disponível em `http://localhost:8000`.

---

## 📜 Documentação da API

A API segue os padrões REST e a documentação interativa está disponível em:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoints Disponíveis

#### Autenticação (`/api/v1/auth`)

- **`POST /signup`**: Cria uma nova conta de usuário.
- **`POST /login`**: Autentica um usuário e retorna um token JWT.
- **`GET /me`**: Retorna os dados do usuário autenticado.

#### Personagens (`/api/v1/characters`)

- **`POST /`**: Cria um novo personagem para o usuário autenticado.
- **`GET /`**: Lista todos os personagens do usuário autenticado.
- **`GET /{character_id}`**: (A ser implementado) Obtém os detalhes de um personagem específico.
- **`DELETE /{character_id}`**: Deleta um personagem do usuário autenticado.

#### Campanha (`/api/v1/campanha`)

- **`POST /`**: (A ser implementado) Inicia uma nova campanha.
- **`GET /{id}`**: (A ser implementado) Retorna o estado atual da campanha.
- **`POST /{id}/acao`**: (A ser implementado) Envia uma ação do jogador e retorna a resposta do LLM.
- **`DELETE /{id}`**: (A ser implementado) Encerra uma campanha.

#### Histórico (`/api/v1/historico`)

- **`GET /{campanha_id}`**: (A ser implementado) Retorna o histórico de interações de uma campanha.
- **`DELETE /{campanha_id}`**: (A ser implementado) Limpa o histórico.

---

## 🗂️ Estrutura de Pastas

A estrutura do projeto foi organizada para separar as responsabilidades, facilitando a manutenção e escalabilidade da API.
```
/
├── app/                  # Contém todo o código fonte da aplicação
│   ├── api/              # Módulos da API (endpoints, dependências)
│   │   └── v1/
│   │       ├── endpoints/  # Arquivos com os endpoints (auth, users, characters)
│   │       └── router.py   # Roteador principal da API v1
│   ├── core/             # Configurações, segurança e lógica principal
│   ├── crud/             # Funções de interação com o banco de dados (Create, Read, Update, Delete)
│   ├── schemas/          # Modelos de dados Pydantic para validação e serialização
│   └── main.py           # Ponto de entrada da aplicação FastAPI
├── .devcontainer/        # Configurações do Dev Container
├── .env.example          # Arquivo de exemplo para variáveis de ambiente
├── requirements.txt      # Dependências de produção
└── requirements-dev.txt  # Dependências de desenvolvimento
```
