from flask import Flask
from geo.api import api
from geo.views import views
from geo.redis_session import RedisSessionInterface

def create_app():
    app = Flask(__name__)
    app.config.from_object('geo.app_config')
    app.session_interface = RedisSessionInterface()
    app.register_blueprint(api)
    app.register_blueprint(views)
    return app
