import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask

from myapp.config import DevelopmentConfig, ProductionConfig


load_dotenv()

def format_duration(seconds):
    if seconds is None:
        return '--:--'
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    env = os.getenv('FLASK_ENV', 'development')
    
    if env == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)


    os.makedirs(app.instance_path, exist_ok=True)

    from myapp.routes import main, auth, playlist, spotify 
    app.register_blueprint(main.main)
    app.register_blueprint(auth.auth)
    app.register_blueprint(playlist.playlist)
    app.register_blueprint(spotify.spotify)


    from myapp.extensions import db, migrate, bcrypt, login_manager
    bcrypt.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db) 


    login_manager.login_view = 'auth.login' 
    login_manager.login_message_category = 'info'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

    app.jinja_env.filters['format_duration'] = format_duration

    return app
