"""
app/controllers/books.py — Blueprint de livros e empréstimos.

Melhorias em relação à versão original:
  - @login_required elimina verificações repetidas.
  - db.session (Flask-SQLAlchemy) — sem sessionmaker manual.
  - Atualização de status "Atrasado" via query bulk (1 UPDATE ao invés de N).
  - Lógica de disponibilidade encapsulada nos modelos (@property).
  - Validações com mensagens claras e retorno consistente.
  - Indentação incorreta da edit_book original corrigida.
  - process_return aceita status "Atrasado" além de "Ativo".
"""

from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from ..extensions import db
from ..models.database import Emprestimo, Livro, Usuario
from .auth import login_required

bp = Blueprint("books", __name__)


# ── Helpers privados ───────────────────────────────────────────────────────

def _sincronizar_atrasos() -> None:
    """
    Atualiza em lote os empréstimos vencidos para status 'Atrasado'.
    Um único UPDATE é muito mais eficiente do que iterar linha a linha.
    """
    db.session.query(Emprestimo).filter(
        Emprestimo.status == "Ativo",
        Emprestimo.data_devolucao_prevista < date.today(),
    ).update({"status": "Atrasado"}, synchronize_session="fetch")
    db.session.commit()


def _int_ou_none(valor: str) -> int | None:
    """Converte string para int; retorna None se vazio ou inválido."""
    try:
        return int(valor) if valor and valor.strip() else None
    except (ValueError, TypeError):
        return None


# ── Livros ────────────────────────────────────────────────────────────────

@bp.route("/books")
@login_required
def list_book():
    """Lista todos os livros ativos do acervo."""
    livros = Livro.query.filter_by(ativo=True).order_by(Livro.titulo).all()
    return render_template("books/list.html", livros=livros)


@bp.route("/books/new", methods=["GET", "POST"])
@login_required
def register_book():
    """Cadastra um novo livro no acervo."""
    if request.method == "POST":
        isbn       = request.form.get("isbn", "").strip()
        titulo     = request.form.get("titulo", "").strip()
        autor      = request.form.get("autor", "").strip()
        editora    = request.form.get("editora", "").strip()
        genero     = request.form.get("genero", "").strip()
        edicao     = request.form.get("edicao", "").strip() or None
        volume     = _int_ou_none(request.form.get("volume", ""))
        publicacao = _int_ou_none(request.form.get("publicacao", ""))
        paginas    = _int_ou_none(request.form.get("paginas", ""))
        exemplares = _int_ou_none(request.form.get("exemplares", ""))

        # Validações de negócio
        if exemplares is None or exemplares < 1:
            flash("A quantidade de exemplares deve ser um número inteiro positivo.", "danger")
            return render_template("books/register.html")

        if isbn and Livro.query.filter_by(isbn=isbn).first():
            flash("Este ISBN já está cadastrado no sistema.", "danger")
            return render_template("books/register.html")

        novo_livro = Livro(
            isbn=isbn or None,
            titulo=titulo,
            autor=autor,
            editora=editora,
            genero_literario=genero,
            edicao=edicao,
            volume=volume,
            ano_publicacao=publicacao,
            numero_paginas=paginas,
            exemplares=exemplares,
            disponiveis=exemplares,
            ativo=True,
        )
        db.session.add(novo_livro)
        db.session.commit()
        flash(f"Livro '{titulo}' cadastrado com sucesso!", "success")
        return redirect(url_for("books.list_book"))

    return render_template("books/register.html")


@bp.route("/books/<string:isbn>/edit", methods=["GET", "POST"])
@login_required
def edit_book(isbn: str):
    """Edita os dados de um livro existente."""
    livro = Livro.query.filter_by(isbn=isbn, ativo=True).first_or_404()

    if request.method == "POST":
        novo_isbn      = request.form.get("isbn", "").strip()
        titulo         = request.form.get("titulo", "").strip()
        autor          = request.form.get("autor", "").strip()
        editora        = request.form.get("editora", "").strip()
        genero         = request.form.get("genero", "").strip()
        edicao         = request.form.get("edicao", "").strip() or None
        volume         = _int_ou_none(request.form.get("volume", ""))
        publicacao     = _int_ou_none(request.form.get("publicacao", ""))
        paginas        = _int_ou_none(request.form.get("paginas", ""))
        novos_exemplares = _int_ou_none(request.form.get("exemplares", ""))

        if novos_exemplares is None or novos_exemplares < 0:
            flash("A quantidade de exemplares deve ser um número inteiro não-negativo.", "danger")
            return render_template("books/edit.html", livro=livro)

        # Garante que o novo ISBN não colide com outro livro
        if novo_isbn != livro.isbn:
            if Livro.query.filter(
                Livro.isbn == novo_isbn, Livro.id != livro.id
            ).first():
                flash("Este ISBN já está em uso por outro livro.", "danger")
                return render_template("books/edit.html", livro=livro)

        # Ajusta disponíveis proporcionalmente à mudança de exemplares
        diferenca         = novos_exemplares - livro.exemplares
        novos_disponiveis = max(0, livro.disponiveis + diferenca)

        # Garante que disponíveis nunca supere exemplares
        novos_disponiveis = min(novos_disponiveis, novos_exemplares)

        livro.isbn             = novo_isbn
        livro.titulo           = titulo
        livro.autor            = autor
        livro.editora          = editora
        livro.genero_literario = genero
        livro.edicao           = edicao
        livro.volume           = volume
        livro.ano_publicacao   = publicacao
        livro.numero_paginas   = paginas
        livro.exemplares       = novos_exemplares
        livro.disponiveis      = novos_disponiveis

        db.session.commit()
        flash(f"Livro '{titulo}' atualizado com sucesso!", "success")
        return redirect(url_for("books.list_book"))

    return render_template("books/edit.html", livro=livro)


@bp.route("/books/<string:isbn>/delete", methods=["POST"])
@login_required
def delete_book(isbn: str):
    """Exclusão lógica de livro (ativo = False)."""
    livro = Livro.query.filter_by(isbn=isbn, ativo=True).first_or_404()

    if livro.emprestados > 0:
        flash(
            f"Não é possível excluir '{livro.titulo}': "
            f"há {livro.emprestados} exemplar(es) atualmente emprestado(s).",
            "danger",
        )
        return redirect(url_for("books.list_book"))

    livro.ativo       = False
    livro.disponiveis = 0
    db.session.commit()
    flash(f"Livro '{livro.titulo}' removido do acervo.", "success")
    return redirect(url_for("books.list_book"))


# ── Empréstimos ───────────────────────────────────────────────────────────

@bp.route("/rentals")
@login_required
def list_rentals():
    """Lista empréstimos ativos/atrasados e o histórico de devoluções."""
    _sincronizar_atrasos()

    ativos = (
        Emprestimo.query
        .join(Usuario)
        .join(Livro)
        .filter(
            Emprestimo.status.in_(["Ativo", "Atrasado"]),
            Emprestimo.ativo == True,
        )
        .order_by(Emprestimo.data_devolucao_prevista.asc())
        .all()
    )

    devolvidos = (
        Emprestimo.query
        .join(Usuario)
        .join(Livro)
        .filter(
            Emprestimo.status == "Devolvido",
            Emprestimo.ativo == True,
        )
        .order_by(Emprestimo.data_devolucao_real.desc())
        .limit(50)   # Limita o histórico para não sobrecarregar a página
        .all()
    )

    return render_template(
        "rentals/list.html",
        active_rentals=ativos,
        returned_rentals=devolvidos,
    )


@bp.route("/rentals/new", methods=["GET", "POST"])
@login_required
def register_rental():
    """Registra um novo empréstimo."""
    leitores         = Usuario.query.filter_by(tipo_usuario="Leitor", ativo=True).order_by(Usuario.nome).all()
    livros_disponiveis = (
        Livro.query
        .filter(Livro.ativo == True, Livro.disponiveis > 0)
        .order_by(Livro.titulo)
        .all()
    )

    hoje   = date.today()
    amanha = hoje + timedelta(days=1)

    ctx = dict(
        leitores=leitores,
        livros=livros_disponiveis,
        today_date=hoje.isoformat(),
        tomorrow_date=amanha.isoformat(),
    )

    if request.method == "POST":
        id_usuario = request.form.get("leitor")
        id_livro   = request.form.get("livro")
        data_str   = request.form.get("dataDevolucao", "")

        # Parse da data de devolução
        try:
            data_devolucao = datetime.strptime(data_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            flash("Data de devolução inválida. Use o formato AAAA-MM-DD.", "danger")
            return render_template("rentals/register.html", **ctx)

        if data_devolucao <= hoje:
            flash("A data de devolução prevista deve ser posterior a hoje.", "danger")
            return render_template("rentals/register.html", **ctx)

        livro   = Livro.query.filter_by(id=id_livro, ativo=True).first()
        usuario = Usuario.query.filter_by(id=id_usuario, ativo=True).first()

        if not livro or not usuario:
            flash("Livro ou leitor não encontrado.", "danger")
            return render_template("rentals/register.html", **ctx)

        if livro.disponiveis <= 0:
            flash(f"Não há exemplares disponíveis de '{livro.titulo}'.", "danger")
            return render_template("rentals/register.html", **ctx)

        emprestimo = Emprestimo(
            id_usuario=usuario.id,
            id_livro=livro.id,
            data_emprestimo=datetime.now(),
            data_devolucao_prevista=data_devolucao,
            status="Ativo",
        )
        livro.disponiveis -= 1

        db.session.add(emprestimo)
        db.session.commit()
        flash(
            f"Empréstimo de '{livro.titulo}' para {usuario.nome} registrado com sucesso!",
            "success",
        )
        return redirect(url_for("books.list_rentals"))

    return render_template("rentals/register.html", **ctx)


@bp.route("/rentals/<int:rental_id>/return", methods=["POST"])
@login_required
def process_return(rental_id: int):
    """Registra a devolução de um empréstimo ativo ou atrasado."""
    emprestimo = (
        Emprestimo.query
        .filter(
            Emprestimo.id == rental_id,
            Emprestimo.status.in_(["Ativo", "Atrasado"]),
        )
        .first_or_404()
    )

    emprestimo.status              = "Devolvido"
    emprestimo.data_devolucao_real = datetime.now()

    # Devolve o exemplar ao acervo
    livro = Livro.query.get(emprestimo.id_livro)
    if livro:
        livro.disponiveis = min(livro.disponiveis + 1, livro.exemplares)
    else:
        flash("Atenção: livro original não encontrado no acervo, mas devolução foi registrada.", "warning")

    db.session.commit()
    flash(f"Devolução de '{emprestimo.livro.titulo}' registrada com sucesso!", "success")
    return redirect(url_for("books.list_rentals"))
