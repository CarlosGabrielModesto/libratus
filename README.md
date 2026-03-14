<div align="center">

<img src="app/static/img/logo.png" alt="Libratus Logo" width="90">

# Libratus

**Sistema de Gestão de Biblioteca**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-d71f00?style=flat-square)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/Licença-MIT-2a9d8f?style=flat-square)](LICENSE)

*Gerencie seu acervo com eficiência e elegância.*

</div>

---

## 📋 Sobre o Projeto

O **Libratus** é uma aplicação web full-stack para gestão de bibliotecas, desenvolvida com **Python + Flask** e **SQLite**. Permite o controle completo de usuários, acervo de livros e empréstimos, com interface moderna e responsiva.

Desenvolvido por **Carlos Gabriel dos Santos Modesto** como projeto de portfólio.

---

## ✨ Funcionalidades

| Módulo | Funcionalidades |
|---|---|
| **Autenticação** | Login por CPF + senha criptografada, sessões seguras, logout com confirmação |
| **Usuários** | Cadastro, edição e exclusão lógica de Leitores, Bibliotecários e Administradores |
| **Acervo** | Cadastro, edição e exclusão lógica de livros com controle de exemplares disponíveis |
| **Empréstimos** | Registro de empréstimos, controle de prazos, atualização automática de atrasos e registro de devoluções |
| **Dashboard** | Painel com estatísticas em tempo real (total de livros, empréstimos ativos, atrasos, leitores) e atividades recentes |

---

## 🗂️ Estrutura do Projeto

```
libratus/
│
├── app/
│   ├── __init__.py              ← Application Factory (create_app)
│   ├── extensions.py            ← Instância compartilhada do SQLAlchemy
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py          ← Modelos ORM: Usuario, Livro, Emprestimo
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth.py              ← Blueprint: autenticação e usuários
│   │   └── books.py             ← Blueprint: livros e empréstimos
│   │
│   ├── static/
│   │   ├── css/style.css        ← Estilos globais (sistema de design próprio)
│   │   ├── js/main.js           ← Scripts: alertas, anti-submit, contadores
│   │   └── img/                 ← logo.png · login.png · background.png
│   │
│   └── templates/
│       ├── layout.html          ← Template base (navbar, footer, flash)
│       ├── index.html           ← Página de login
│       ├── dashboard.html       ← Painel gerencial
│       ├── books/               ← list · register · edit
│       ├── users/               ← list · register · edit
│       ├── rentals/             ← list · register
│       └── errors/              ← 404 · 500
│
├── data/                        ← Banco de dados SQLite (gitignored)
├── .env                         ← Variáveis de ambiente (gitignored)
├── .env.example                 ← Modelo de configuração
├── .gitignore
├── requirements.txt
├── seed.py                      ← Popula o banco com dados iniciais
├── wsgi.py                      ← Entry point (dev e produção)
└── README.md
```

---

## 🚀 Como Executar

### Pré-requisitos

- Python **3.11+**
- pip

### 1. Clone o repositório

```bash
git clone https://github.com/carlosmodesto/libratus.git
cd libratus
```

### 2. Crie e ative o ambiente virtual

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e defina uma `SECRET_KEY` segura:

```bash
# Gere uma chave com:
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Popule o banco de dados

```bash
python seed.py
```

Isso cria o banco de dados, as tabelas e um usuário administrador padrão:

| Campo | Valor |
|---|---|
| CPF | `000.000.000-00` |
| Senha | `admin123` |

> ⚠️ **Altere a senha do administrador após o primeiro acesso.**

### 6. Inicie o servidor

```bash
python wsgi.py
```

Acesse: **[http://localhost:5000](http://localhost:5000)**

---

## 🌐 Deploy em Produção (Gunicorn)

```bash
gunicorn wsgi:app \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

> Recomenda-se utilizar um proxy reverso (Nginx) na frente do Gunicorn em produção.

---

## 🗄️ Banco de Dados

O Libratus utiliza **SQLite 3** via **Flask-SQLAlchemy**. O schema é criado automaticamente ao iniciar a aplicação.

### Modelos

```
Usuario
  id · nome · cpf (único) · nascimento · endereco
  telefone · email (único) · senha (hash) · tipo_usuario · ativo

Livro
  id · titulo · isbn (único) · autor · editora · edicao
  volume · genero_literario · numero_paginas · ano_publicacao
  exemplares · disponiveis · ativo

Emprestimo
  id · id_usuario (FK) · id_livro (FK)
  data_emprestimo · data_devolucao_prevista · data_devolucao_real
  status [Ativo | Atrasado | Devolvido] · ativo
```

### Índices criados

- `usuario.cpf` — login por CPF
- `livro.isbn` — busca e unicidade
- `emprestimo.status` — filtros de listagem
- `emprestimo(status, data_devolucao_prevista)` — atualização em lote de atrasos

---

## 🎨 Design System

A interface utiliza um sistema de design próprio construído sobre **Bootstrap 5.3** com variáveis CSS customizadas.

| Token | Valor | Uso |
|---|---|---|
| `--clr-primary` | `#0a9396` | Ações primárias, links, navbar ativa |
| `--clr-primary-dark` | `#005f73` | Títulos, hover, gradientes |
| `--clr-accent` | `#ee9b00` | Edição, avisos, botão de logout |
| `--clr-danger` | `#e63946` | Exclusão, erros |
| `--clr-success` | `#2a9d8f` | Confirmações |

---

## 🔒 Segurança

- Senhas armazenadas com **PBKDF2-SHA256** via Werkzeug
- Sessões protegidas com `SECRET_KEY` via variável de ambiente
- `SESSION_COOKIE_HTTPONLY = True` e `SESSION_COOKIE_SAMESITE = "Lax"`
- Decorator `@login_required` em todas as rotas autenticadas
- Exclusão lógica em vez de remoção física dos registros
- Proteção contra auto-exclusão de usuário logado
- Impedimento de exclusão com empréstimos ativos

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| **Back-end** | Python 3.11 · Flask 3.0 · Flask-SQLAlchemy · Werkzeug |
| **Banco de dados** | SQLite 3 (SQLAlchemy ORM) |
| **Front-end** | HTML5 · CSS3 (variáveis customizadas) · JavaScript ES6+ |
| **UI Framework** | Bootstrap 5.3 · Bootstrap Icons 1.11 |
| **Tipografia** | Inter (Google Fonts) |
| **Produção** | Gunicorn |

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.

---

<div align="center">

Desenvolvido com ♥ por **Carlos Gabriel dos Santos Modesto**

</div>
