# app/controllers/auth_controller.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse, urljoin

from app import db
from app.models.user import User
from app.models.post import Post  # 👈 Necesario para mostrar posts

auth_bp = Blueprint('auth', __name__)

# -------------------------
# Función auxiliar
# -------------------------
def _is_safe_url(target: str) -> bool:
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (test_url.scheme in ('http', 'https')) and (ref_url.netloc == test_url.netloc)

# -------------------------
# Login
# -------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('¡Bienvenido!', 'success')

            next_page = request.args.get('next')
            if next_page and _is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

# -------------------------
# Dashboard (ahora foro principal)
# -------------------------
@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Portada principal del foro."""
    try:
        return render_template('forum/forums.html')  # 👈 Usa tu nueva plantilla
    except Exception as e:
        from flask import current_app
        current_app.logger.exception("Error renderizando forums.html")
        return f"<pre>Dashboard ERROR:\n{e}</pre>", 500

# -------------------------
# Vista de publicaciones (listado)
# -------------------------
@auth_bp.route('/dashboard/posts')
@login_required
def dashboard_posts():
    """Listado de publicaciones del foro."""
    return render_template('forum/posts.html')

# -------------------------
# Detalle de publicación individual
# -------------------------
@auth_bp.route('/dashboard/posts/<int:post_id>')
@login_required
def dashboard_detail(post_id):
    """Vista detalle de una publicación individual."""
    post = Post.query.get_or_404(post_id)
    return render_template(
        'forum/detail.html',
        post_title=(post.content[:42] + '…') if len(post.content) > 45 else post.content,
        post_author=getattr(post.author, 'nombre', getattr(post.author, 'email', 'Usuario')),
        post_content=post.content
    )

# -------------------------
# Logout
# -------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('auth.login_page'))

# -------------------------
# Registro
# -------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        if not nombre or not email or not password:
            flash('Todos los campos son obligatorios.', 'warning')
            return render_template('register.html', nombre=nombre, email=email)

        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('register.html', nombre=nombre, email=email)

        if User.query.filter_by(email=email).first():
            flash('El correo electrónico ya está registrado.', 'danger')
            return render_template('register.html', nombre=nombre, email=email)

        try:
            user = User(nombre=nombre, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Cuenta creada con éxito. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login_page'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {e}', 'danger')
            return render_template('register.html', nombre=nombre, email=email)

    return render_template('register.html')


# Vista para crear publicación desde UI
@forum_bp.get("/publicar")
@login_required
def publicar():
    return render_template("forum/detail.html")
