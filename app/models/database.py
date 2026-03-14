"""
app/models/database.py — Modelos ORM da aplicação.

Usa Flask-SQLAlchemy (db.Model) importado via app.extensions para
evitar importações circulares com a factory function.

Melhorias em relação à versão original:
  - Relacionamentos com lazy="select" explícito.
  - @property encapsula lógica de negócio (emprestados, disponivel, esta_atrasado).
  - Índices nos campos mais consultados (isbn, cpf, status, devolucao).
  - __repr__ padronizados e informativos.
  - criar_tabelas() centraliza a criação do schema.
"""

from datetime import date, datetime
from sqlalchemy import Index
from ..extensions import db


class Usuario(db.Model):
    """Usuário do sistema: Bibliotecário, Leitor ou Administrador."""

    __tablename__ = "usuario"

    id           = db.Column(db.Integer, primary_key=True)
    nome         = db.Column(db.String(100), nullable=False)
    cpf          = db.Column(db.String(14), unique=True, nullable=False, index=True)
    nascimento   = db.Column(db.Date, nullable=False)
    endereco     = db.Column(db.Text, nullable=False, default="")
    telefone     = db.Column(db.String(20), nullable=False, default="")
    email        = db.Column(db.String(255), unique=True, nullable=False)
    senha        = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)
    ativo        = db.Column(db.Boolean, default=True, nullable=False)

    emprestimos = db.relationship(
        "Emprestimo",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def tem_emprestimos_ativos(self) -> bool:
        """Verifica se há empréstimos não devolvidos vinculados ao usuário."""
        return any(e.status in ("Ativo", "Atrasado") for e in self.emprestimos)

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} nome='{self.nome}' tipo='{self.tipo_usuario}'>"

    def __str__(self) -> str:
        return self.nome


class Livro(db.Model):
    """Livro do acervo da biblioteca."""

    __tablename__ = "livro"

    id               = db.Column(db.Integer, primary_key=True)
    titulo           = db.Column(db.String(200), nullable=False)
    isbn             = db.Column(db.String(25), unique=True, nullable=False, index=True)
    autor            = db.Column(db.Text, nullable=False)
    editora          = db.Column(db.String(100), nullable=False, default="")
    edicao           = db.Column(db.String(50), nullable=True)
    volume           = db.Column(db.Integer, nullable=True)
    genero_literario = db.Column(db.String(100), nullable=False, default="")
    numero_paginas   = db.Column(db.Integer, nullable=True)
    ano_publicacao   = db.Column(db.Integer, nullable=True)
    exemplares       = db.Column(db.Integer, nullable=False, default=1)
    disponiveis      = db.Column(db.Integer, nullable=False, default=1)
    ativo            = db.Column(db.Boolean, default=True, nullable=False)

    emprestimos = db.relationship(
        "Emprestimo",
        back_populates="livro",
        cascade="all, delete-orphan",
        lazy="select",
    )

    @property
    def emprestados(self) -> int:
        """Exemplares atualmente fora da biblioteca."""
        return self.exemplares - self.disponiveis

    @property
    def disponivel(self) -> bool:
        return self.disponiveis > 0 and self.ativo

    def __repr__(self) -> str:
        return f"<Livro id={self.id} titulo='{self.titulo}' isbn='{self.isbn}'>"

    def __str__(self) -> str:
        return self.titulo


class Emprestimo(db.Model):
    """Registro de empréstimo de um livro a um leitor."""

    __tablename__ = "emprestimo"

    # Índice composto para queries de status + vencimento (muito frequentes)
    __table_args__ = (
        Index("ix_emprestimo_status_vencimento", "status", "data_devolucao_prevista"),
    )

    id                      = db.Column(db.Integer, primary_key=True)
    id_usuario              = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    id_livro                = db.Column(db.Integer, db.ForeignKey("livro.id"), nullable=False)
    data_emprestimo         = db.Column(db.DateTime, nullable=False, default=datetime.now)
    data_devolucao_prevista = db.Column(db.Date, nullable=False)
    data_devolucao_real     = db.Column(db.DateTime, nullable=True)
    status                  = db.Column(db.String(25), nullable=False, default="Ativo", index=True)
    ativo                   = db.Column(db.Boolean, default=True, nullable=False)

    usuario = db.relationship("Usuario", back_populates="emprestimos", lazy="select")
    livro   = db.relationship("Livro",   back_populates="emprestimos", lazy="select")

    @property
    def esta_atrasado(self) -> bool:
        return self.status == "Ativo" and self.data_devolucao_prevista < date.today()

    @property
    def dias_atraso(self) -> int:
        if self.esta_atrasado:
            return (date.today() - self.data_devolucao_prevista).days
        return 0

    def __repr__(self) -> str:
        return (
            f"<Emprestimo id={self.id} livro_id={self.id_livro} "
            f"usuario_id={self.id_usuario} status='{self.status}'>"
        )


def criar_tabelas() -> None:
    """Cria todas as tabelas no banco de dados (idempotente)."""
    db.create_all()
