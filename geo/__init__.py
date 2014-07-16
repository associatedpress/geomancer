from flask import Flask
from geo.api import api
from geo.redis_session import RedisSessionInterface

def create_app():
    app = Flask(__name__)
    app.config.from_object('geo.app_config')
    app.session_interface = RedisSessionInterface()
    app.register_blueprint(api)
    return app
