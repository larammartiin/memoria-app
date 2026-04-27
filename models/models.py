from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='familiar')
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    perfiles = db.relationship('PerfilMayor', backref='familiar', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class PerfilMayor(db.Model):
    __tablename__ = 'perfiles_mayores'

    id = db.Column(db.Integer, primary_key=True)
    familiar_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer)
    ciudad_natal = db.Column(db.String(100))
    nombre_pareja = db.Column(db.String(100))
    nombres_hijos = db.Column(db.String(500))
    nombres_nietos = db.Column(db.String(500))
    nombre_mejor_amigo = db.Column(db.String(100))
    lugar_veraneo = db.Column(db.String(200))
    viajes_favoritos = db.Column(db.String(500))
    aficiones = db.Column(db.String(500))
    comida_favorita = db.Column(db.String(200))
    pelicula_favorita = db.Column(db.String(200))
    recuerdos_especiales = db.Column(db.Text)
    nombre_mascota = db.Column(db.String(100))
    tipo_mascota = db.Column(db.String(100))
    informacion_adicional = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sesiones = db.relationship('Sesion', backref='perfil', lazy=True)


class Sesion(db.Model):
    __tablename__ = 'sesiones'

    id = db.Column(db.Integer, primary_key=True)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfiles_mayores.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total_preguntas = db.Column(db.Integer, default=0)
    respuestas_correctas = db.Column(db.Integer, default=0)
    respuestas_incorrectas = db.Column(db.Integer, default=0)
    preguntas_pasadas = db.Column(db.Integer, default=0)
    tiempo_total = db.Column(db.Integer, default=0)
    tipo_juego = db.Column(db.String(20), default='rosco')

    preguntas = db.relationship('Pregunta', backref='sesion', lazy=True)


class Pregunta(db.Model):
    __tablename__ = 'preguntas'

    id = db.Column(db.Integer, primary_key=True)
    sesion_id = db.Column(db.Integer, db.ForeignKey('sesiones.id'), nullable=False)
    letra = db.Column(db.String(1), nullable=False)
    texto_pregunta = db.Column(db.Text, nullable=False)
    respuesta_correcta = db.Column(db.String(200), nullable=False)
    respuesta_usuario = db.Column(db.String(200))
    es_correcta = db.Column(db.Boolean)
    tiempo_respuesta = db.Column(db.Integer)
    pista = db.Column(db.String(300))
    