from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from redis import Redis
import rq
from os import environ

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():

    app = Flask(__name__, instance_relative_config=False)

    if environ.get('FLASK_ENV') == 'production':
        app.config.from_object('config.ProdConfig')
    else:
        app.config.from_object('config.DevConfig')

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue(app.config['REDIS_QUEUE'], connection=app.redis)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        from . import models
        from . import auth
        from . import main
    
        app.register_blueprint(auth.bp)
        app.register_blueprint(main.bp)
    
        db.create_all()

        return app