from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from models.models import db, Usuario
import os
import math

load_dotenv()

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'clave_secreta_default')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///memoria.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth
    from routes.perfil import perfil
    from routes.juego import juego

    app.register_blueprint(auth)
    app.register_blueprint(perfil)
    app.register_blueprint(juego)

    app.jinja_env.globals['round'] = round

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
    

