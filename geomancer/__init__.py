from flask import Flask, render_template
from geomancer.api import api
from geomancer.views import views
from geomancer.redis_session import RedisSessionInterface

try:
    from raven.contrib.flask import Sentry
    from geomancer.app_config import SENTRY_DSN
    sentry = Sentry(dsn=SENTRY_DSN)
except ImportError:
    sentry = None
except KeyError:
    sentry = None

def create_app():
    app = Flask(__name__)
    app.config.from_object('geomancer.app_config')
    app.session_interface = RedisSessionInterface()
    app.register_blueprint(api)
    app.register_blueprint(views)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html'), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return render_template('413.html'), 413
    
    @app.template_filter('string_split')
    def string_split(val, splitter):
        return val.split(splitter)

    if sentry:
        sentry.init_app(app)

    return app
