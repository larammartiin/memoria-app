from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from models.models import Usuario, db

auth = Blueprint('auth', __name__)

@auth.route('/', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario or not usuario.check_password(password):
            return render_template('login.html', error='Email o contraseña incorrectos')
        
        login_user(usuario)
        return redirect(url_for('perfil.seleccion_rol'))
    
    return render_template('login.html')


@auth.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nombre = request.form.get('nombre')
        
        usuario_existe = Usuario.query.filter_by(email=email).first()
        if usuario_existe:
            return render_template('registro.html', error='Este email ya está registrado')
        
        nuevo_usuario = Usuario(email=email, nombre=nombre,
            pregunta_seguridad=request.form.get('pregunta_seguridad', ''),
            respuesta_seguridad=request.form.get('respuesta_seguridad', '').strip().lower())
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        login_user(nuevo_usuario)
        return redirect(url_for('perfil.seleccion_rol'))
    
    return render_template('registro.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

from flask import send_from_directory
import os

@auth.route('/sw.js')
def service_worker():
    return send_from_directory(os.path.join(os.path.dirname(os.path.dirname(__file__))), 'sw.js', mimetype='application/javascript')

@auth.route('/olvide-contrasena', methods=['GET', 'POST'])
def olvide_contrasena():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        usuario = Usuario.query.filter_by(email=email).first()
        if not usuario:
            return render_template('olvide_contrasena.html', error='No existe ninguna cuenta con ese email.')
        return redirect(url_for('auth.pregunta_seguridad', email=email))
    return render_template('olvide_contrasena.html')


@auth.route('/pregunta-seguridad', methods=['GET', 'POST'])
def pregunta_seguridad():
    email = request.args.get('email') or request.form.get('email')
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        respuesta = request.form.get('respuesta', '').strip().lower()
        if respuesta == usuario.respuesta_seguridad:
            return redirect(url_for('auth.nueva_contrasena', email=email))
        return render_template('pregunta_seguridad.html',
            pregunta=usuario.pregunta_seguridad,
            email=email,
            error='Respuesta incorrecta. Inténtalo de nuevo.')

    return render_template('pregunta_seguridad.html',
        pregunta=usuario.pregunta_seguridad,
        email=email)


@auth.route('/nueva-contrasena', methods=['GET', 'POST'])
def nueva_contrasena():
    email = request.args.get('email') or request.form.get('email')
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        from werkzeug.security import generate_password_hash
        nueva = request.form.get('nueva_contrasena', '').strip()
        confirmar = request.form.get('confirmar_contrasena', '').strip()
        if nueva != confirmar:
            return render_template('nueva_contrasena.html', email=email, error='Las contraseñas no coinciden.')
        if len(nueva) < 6:
            return render_template('nueva_contrasena.html', email=email, error='La contraseña debe tener al menos 6 caracteres.')
        usuario.password_hash = generate_password_hash(nueva)
        db.session.commit()
        return redirect(url_for('auth.login', mensaje='Contraseña cambiada correctamente. Ya puedes iniciar sesión.'))

    return render_template('nueva_contrasena.html', email=email)
