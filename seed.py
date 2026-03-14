"""
seed.py — Popula o banco de dados com dados iniciais para desenvolvimento/teste.

Uso:
    python seed.py

Cria um usuário administrador padrão e alguns livros de exemplo.
"""

from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models.database import Usuario, Livro


ADMIN_CPF   = "000.000.000-00"
ADMIN_SENHA = "admin123"

LIVROS_EXEMPLO = [
    {
        "titulo": "Clean Code: A Handbook of Agile Software Craftsmanship",
        "isbn": "978-0132350884",
        "autor": "Robert C. Martin",
        "editora": "Prentice Hall",
        "genero_literario": "Tecnologia",
        "edicao": "1ª Edição",
        "volume": None,
        "numero_paginas": 464,
        "ano_publicacao": 2008,
        "exemplares": 3,
    },
    {
        "titulo": "O Senhor dos Anéis: A Sociedade do Anel",
        "isbn": "978-8533613379",
        "autor": "J.R.R. Tolkien",
        "editora": "Martins Fontes",
        "genero_literario": "Fantasia",
        "edicao": "1ª Edição",
        "volume": 1,
        "numero_paginas": 576,
        "ano_publicacao": 2001,
        "exemplares": 2,
    },
    {
        "titulo": "Dom Casmurro",
        "isbn": "978-8572329491",
        "autor": "Machado de Assis",
        "editora": "Ateliê Editorial",
        "genero_literario": "Romance",
        "edicao": "1ª Edição",
        "volume": None,
        "numero_paginas": 256,
        "ano_publicacao": 1899,
        "exemplares": 5,
    },
]


def seed() -> None:
    app = create_app()

    with app.app_context():
        # Cria administrador se não existir
        if not Usuario.query.filter_by(cpf=ADMIN_CPF).first():
            admin = Usuario(
                nome="Administrador",
                cpf=ADMIN_CPF,
                nascimento=date(1990, 1, 1),
                endereco="Biblioteca Central",
                telefone="(00) 00000-0000",
                email="admin@libratus.com",
                senha=generate_password_hash(ADMIN_SENHA, method="pbkdf2:sha256"),
                tipo_usuario="Administrador",
                ativo=True,
            )
            db.session.add(admin)
            print(f"✅  Administrador criado — CPF: {ADMIN_CPF} | Senha: {ADMIN_SENHA}")
        else:
            print("ℹ️   Administrador já existe, pulando.")

        # Cria livros de exemplo
        for dados in LIVROS_EXEMPLO:
            if not Livro.query.filter_by(isbn=dados["isbn"]).first():
                livro = Livro(**dados, disponiveis=dados["exemplares"], ativo=True)
                db.session.add(livro)
                print(f"✅  Livro criado: {dados['titulo']}")
            else:
                print(f"ℹ️   Livro já existe: {dados['titulo']}")

        db.session.commit()
        print("\n🎉  Seed concluído com sucesso!")


if __name__ == "__main__":
    seed()
