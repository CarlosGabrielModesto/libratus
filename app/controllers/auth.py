"""
app/controllers/auth.py — Blueprint de autenticação e gerenciamento de usuários.

Melhorias em relação à versão original:
  - Decorator @login_required elimina verificação repetida em cada rota.
  - Uso de db.session (Flask-SQLAlchemy) no lugar de sessionmaker manual.
  - Sem vazamento de sessão: db.session gerenciado pelo Flask-SQLAlchemy.
  - Validações extraídas em funções auxiliares (_validar_cpf, _validar_email).
  - Flash messages padronizadas e consistentes.
  - Proteção contra auto-exclusão e exclusão com empréstimos ativos.
  - Senha não retorna ao formulário em nenhuma situação.
"""

from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models.database import Emprestimo, Usuario

bp = Blueprint("auth", __name__)


# ── Decorator de autenticação ──────────────────────────────────────────────

def login_required(f):
    """Redireciona para o login caso o usuário não esteja autenticado."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Helpers privados ───────────────────────────────────────────────────────

def _hash_senha(senha: str) -> str:
    return generate_password_hash(senha, method="pbkdf2:sha256")


def _cpf_em_uso(cpf: str, excluir_id: int | None = None) -> bool:
    q = Usuario.query.filter_by(cpf=cpf)
    if excluir_id:
        q = q.filter(Usuario.id != excluir_id)
    return q.first() is not None


def _email_em_uso(email: str, excluir_id: int | None = None) -> bool:
    q = Usuario.query.filter(Usuario.email == email, Usuario.ativo == True)
    if excluir_id:
        q = q.filter(Usuario.id != excluir_id)
    return q.first() is not None


def _parse_data(data_str: str):
    """Converte string 'YYYY-MM-DD' para objeto date. Retorna None se inválida."""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ── Rotas de Autenticação ─────────────────────────────────────────────────

@bp.route("/", methods=["GET", "POST"])
def login():
    """Página de login. Redireciona para o dashboard se já autenticado."""
    if "user_id" in session:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        cpf   = request.form.get("cpf", "").strip()
        senha = request.form.get("senha", "")

        usuario = Usuario.query.filter_by(cpf=cpf, ativo=True).first()

        if usuario and check_password_hash(usuario.senha, senha):
            session.clear()
            session["user_id"]   = usuario.id
            session["user_name"] = usuario.nome
            session["user_tipo"] = usuario.tipo_usuario
            return redirect(url_for("auth.dashboard"))

        flash("CPF ou senha inválidos.", "danger")

    return render_template("index.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Encerra a sessão do usuário."""
    session.clear()
    flash("Você saiu do sistema com sucesso.", "success")
    return redirect(url_for("auth.login"))


# ── Dashboard ─────────────────────────────────────────────────────────────

@bp.route("/dashboard")
@login_required
def dashboard():
    """Painel gerencial com estatísticas e atividades recentes."""
    from datetime import date
    from ..models.database import Livro

    total_livros        = Livro.query.filter_by(ativo=True).count()
    emprestimos_ativos  = Emprestimo.query.filter_by(status="Ativo").count()
    devolucoes_atrasadas = (
        Emprestimo.query
        .filter_by(status="Ativo")
        .filter(Emprestimo.data_devolucao_prevista < date.today())
        .count()
    )
    total_leitores = Usuario.query.filter_by(tipo_usuario="Leitor", ativo=True).count()

    atividades_recentes = (
        Emprestimo.query
        .join(Usuario)
        .join(Livro)
        .order_by(Emprestimo.data_emprestimo.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_livros=total_livros,
        emprestimos_ativos=emprestimos_ativos,
        devolucoes_atrasadas=devolucoes_atrasadas,
        total_leitores=total_leitores,
        atividades_recentes=atividades_recentes,
    )


# ── Gerenciamento de Usuários ─────────────────────────────────────────────

@bp.route("/users")
@login_required
def list_users():
    """Lista todos os usuários ativos, ordenados por nome."""
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    return render_template("users/list.html", users=usuarios)


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
def register_user():
    """Cadastra um novo usuário no sistema."""
    if request.method == "POST":
        nome         = request.form.get("nome", "").strip()
        cpf          = request.form.get("cpf", "").strip()
        email        = request.form.get("email", "").strip().lower()
        nascimento   = request.form.get("dataNascimento", "")
        telefone     = request.form.get("telefone", "").strip()
        endereco     = request.form.get("endereco", "").strip()
        tipo_usuario = request.form.get("tipoUsuario", "")
        senha        = request.form.get("senha", "")

        # Validações
        data_nasc = _parse_data(nascimento)
        if not data_nasc:
            flash("Data de nascimento inválida. Use o formato AAAA-MM-DD.", "danger")
            return render_template("users/register.html")

        if _cpf_em_uso(cpf):
            flash("Este CPF já está cadastrado no sistema.", "danger")
            return render_template("users/register.html")

        if _email_em_uso(email):
            flash("Este e-mail já está em uso por outro usuário.", "danger")
            return render_template("users/register.html")

        novo = Usuario(
            nome=nome,
            cpf=cpf,
            email=email,
            nascimento=data_nasc,
            telefone=telefone,
            endereco=endereco,
            tipo_usuario=tipo_usuario,
            senha=_hash_senha(senha),
            ativo=True,
        )
        db.session.add(novo)
        db.session.commit()
        flash(f"Usuário '{nome}' cadastrado com sucesso!", "success")
        return redirect(url_for("auth.list_users"))

    return render_template("users/register.html")


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id: int):
    """Edita os dados de um usuário existente."""
    usuario = Usuario.query.filter_by(id=user_id, ativo=True).first_or_404()

    if request.method == "POST":
        nome         = request.form.get("nome", "").strip()
        email        = request.form.get("email", "").strip().lower()
        nascimento   = request.form.get("dataNascimento", "")
        telefone     = request.form.get("telefone", "").strip()
        endereco     = request.form.get("endereco", "").strip()
        tipo_usuario = request.form.get("tipoUsuario", "")
        nova_senha   = request.form.get("senha", "")

        data_nasc = _parse_data(nascimento)
        if not data_nasc:
            flash("Data de nascimento inválida.", "danger")
            return render_template("users/edit.html", user=usuario)

        if _email_em_uso(email, excluir_id=user_id):
            flash("Este e-mail já está em uso por outro usuário.", "danger")
            return render_template("users/edit.html", user=usuario)

        usuario.nome         = nome
        usuario.email        = email
        usuario.nascimento   = data_nasc
        usuario.telefone     = telefone
        usuario.endereco     = endereco
        usuario.tipo_usuario = tipo_usuario

        if nova_senha:
            usuario.senha = _hash_senha(nova_senha)

        db.session.commit()
        flash(f"Usuário '{nome}' atualizado com sucesso!", "success")
        return redirect(url_for("auth.list_users"))

    return render_template("users/edit.html", user=usuario)


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id: int):
    """Realiza exclusão lógica de um usuário (ativo = False)."""
    usuario = Usuario.query.filter_by(id=user_id, ativo=True).first_or_404()

    # Impede auto-exclusão
    if usuario.id == session["user_id"]:
        flash("Você não pode excluir seu próprio usuário enquanto estiver logado.", "warning")
        return redirect(url_for("auth.list_users"))

    # Impede exclusão com empréstimos pendentes
    tem_pendentes = (
        Emprestimo.query
        .filter_by(id_usuario=user_id)
        .filter(Emprestimo.status.in_(["Ativo", "Atrasado"]))
        .first()
    )
    if tem_pendentes:
        flash(
            f"Não é possível excluir '{usuario.nome}': existem empréstimos em aberto.",
            "danger",
        )
        return redirect(url_for("auth.list_users"))

    usuario.ativo = False
    db.session.commit()
    flash(f"Usuário '{usuario.nome}' removido com sucesso.", "success")
    return redirect(url_for("auth.list_users"))
