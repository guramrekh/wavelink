import os
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask

load_dotenv()

def format_duration(seconds):
    if seconds is None:
        return '--:--'
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'myapp.sqlite'),

        SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID'),
        SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from myapp.routes import main, auth, playlist, spotify 
    app.register_blueprint(main.main)
    app.register_blueprint(auth.auth)
    app.register_blueprint(playlist.playlist)
    app.register_blueprint(spotify.spotify)


    from myapp.extensions import db, bcrypt, login_manager
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login' 
    login_manager.login_message_category = 'info'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)


    app.jinja_env.filters['format_duration'] = format_duration

    return app
