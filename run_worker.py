from geo.worker import queue_daemon
from geo import create_app

app = create_app()

queue_daemon(app)
