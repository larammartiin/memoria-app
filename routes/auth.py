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
        return redirect(url_for('perfil.inicio'))
    
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
        
        nuevo_usuario = Usuario(email=email, nombre=nombre)
        nuevo_usuario.set_password(password)
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        login_user(nuevo_usuario)
        return redirect(url_for('perfil.inicio'))
    
    return render_template('registro.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
